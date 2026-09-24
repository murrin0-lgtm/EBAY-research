"""Lab 10: eBay five-year pro forma and discounted FCFE valuation.

Run: py ebay_proforma.py
Checks, including deliberate failures: py ebay_proforma.py --self-test
Save the report: py ebay_proforma.py --output ebay_proforma_output.txt
Standard library only. USD millions, shares in millions, except per-share values.
Opening/valuation date: 2025-12-31; forecasts: FY2026-FY2030, year-end discounting.
Inputs transcribed from lab10_notes.md and the three linked 10-Ks; no live downloads.
See ebay_proforma_model_notes.md for additional modelling judgments and limitations.
"""

import argparse
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from math import isfinite
from pathlib import Path

SOURCES = {
    2023: 'https://www.sec.gov/Archives/edgar/data/1065088/000106508824000036/ebay-20231231.htm',
    2024: 'https://www.sec.gov/Archives/edgar/data/1065088/000106508825000037/ebay-20241231.htm',
    2025: 'https://www.sec.gov/Archives/edgar/data/1065088/000106508826000027/ebay-20251231.htm',
}
# HISTORY: each column comes from that year's filing: income statement,
# balance sheet, cash-flow statement, PP&E note, and MD&A growth table.
HISTORY = {
    2023: dict(revenue=10112., gross_profit=7279., sga=3413., net_income=2767.,
               ppe=1243., equity=6396., depreciation=441., capex=456.),
    2024: dict(revenue=10283., gross_profit=7403., sga=3233., net_income=1975.,
               ppe=1263., equity=5158., depreciation=370., capex=458.),
    2025: dict(revenue=11100., gross_profit=7931., sga=3592., net_income=2031.,
               ppe=1338., equity=4615., depreciation=421., capex=525.),
}
YEARS = tuple(range(2026, 2031))
TOL = 1e-6
MARKET_PRICE = 107.83
MARKET_DATE = '2026-09-24 regular-session close (4:00 PM EDT)'
MARKET_SOURCE = 'https://stockanalysis.com/stocks/ebay/history/'

# EDITABLE JUDGMENTS from lab10_notes.md. Historical ratios used in future years
# are forecasts (judgments), even though their starting values are historical.
ASSUMPTIONS = dict(
    growth=.04,                    # Moderate growth within the historical range.
    gross_margin=7931 / 11100,      # Maintain 2025 gross margin.
    sga_ratio=3592 / 7931,          # Maintain 2025 SG&A / gross profit.
    product_development_ratio=.148,  # Technology spending grows with revenue.
    transaction_loss_ratio=.036,   # Losses grow with marketplace activity.
    depreciation_ratio=421 / 1338,  # Apply latest ratio to OPENING net PP&E.
    capex_ratio=525 / 11100,        # Investment spending grows with revenue.
    amortization=24.,              # Hold separate acquired-intangible expense flat.
    tax_rate=.20,                  # Normalized rate between recent annual rates.
    impairment=0.,                 # No new specific impairment assumed.
    min_cash=1000.,                # Corporate operating cash reserve.
    repayment=250.,                # Net debt reduction; assumes refinancing.
    debt_rate=.04,                 # Simplified rate on opening debt.
    buyback=1000.,                 # Lower repurchases than in 2025.
    dividends=550.,                # Payments near recent annual level.
    revolver_limit=2000.,          # Historical size; renewal past Jan 2029 assumed.
    revolver_rate=.06,             # Higher emergency borrowing cost.
    working_capital_ratio=.01,     # Incremental operating assets / revenue increase.
    cost_of_equity=.10,            # Scenario required return, not CAPM.
    terminal_growth=.025,          # Slower growth after the explicit forecast.
    shares=449.,                   # HISTORY: 2025 year-end shares, not diluted EPS.
)

# HISTORY: 2025 10-K consolidated balance sheet, p. 61.
# Regrouping is arithmetic, not a forecast plug.
OPENING = dict(
    year=2025, revenue=11100., cash=1867., investments=1052. + 2767.,
    customer_receivable=1280., ppe=1338.,
    other_assets=887. + 4467. + 428. + 2959. + 565.,
    debt=750. + 5996., customer_payable=1280.,
    other_liabilities=242. + 2257. + 108. + 315. + 1472. + 575.,
    equity=4615., revolver=0., inventory=0., floor=0.,
)

# ADDITIONAL JUDGMENTS required to close the model, explained in the companion MD:
# Customer receivable/payable grow together at revenue growth; investments and
# other liabilities stay flat. Other assets change only by incremental working
# capital, amortization and impairment. No acquisitions, investment income/gains,
# discontinued operations, OCI, or new stock issuance are projected.
# SBC is treated as cash-equivalent compensation: no addback and no dilution.
# Transaction-loss cash settlements equal expense; cash taxes equal tax expense.
# PP&E depreciation is ALREADY included in GAAP margin/expense assumptions.
# Add it back in CFO and reduce PP&E, but do not deduct it again from EBIT.
# Value excludes investment income, then adds investments at carrying value and
# opening cash above the reserve once. No tax/liquidity haircut is assumed.
# Do not add ending cash: forecast FCFE already includes retained cash generation.


def totals(r):
    assets = sum(r[k] for k in ('cash', 'investments', 'customer_receivable',
                                'ppe', 'other_assets', 'inventory'))
    liabilities = sum(r[k] for k in ('debt', 'customer_payable',
                                     'other_liabilities', 'revolver', 'floor'))
    return assets, liabilities


def balance_gap(r):
    assets, liabilities = totals(r)
    return assets - liabilities - r['equity']


def require_zero(year, name, gap):
    if not isfinite(gap) or abs(gap) > TOL:
        raise ValueError(f'FY{year}: {name}; gap {gap:,.6f} million')


def validate_inputs(a, opening):
    for name, value in a.items():
        if not isfinite(value):
            raise ValueError(f'{name} must be finite')
    for name, value in opening.items():
        if not isfinite(value):
            raise ValueError(f'Opening {name} must be finite')
    if a['growth'] <= -1 or a['terminal_growth'] <= -1:
        raise ValueError('Growth must exceed -100%')
    if a['cost_of_equity'] <= max(0., a['terminal_growth']):
        raise ValueError('Cost of equity must be positive and exceed terminal growth')
    if a['shares'] <= 0:
        raise ValueError('Shares must be positive')
    for key in ('gross_margin', 'tax_rate', 'depreciation_ratio'):
        if not 0 <= a[key] <= 1:
            raise ValueError(f'{key} must be between 0 and 1')
    for key in a.keys() - {'growth', 'terminal_growth'}:
        if a[key] < 0:
            raise ValueError(f'{key} cannot be negative')
    require_zero(opening['year'], 'opening balance sheet', balance_gap(opening))


def check_rows(rows, a, opening):
    """Independent links checked before printing any valuation; never plug a gap."""
    if len(rows) != 5 or tuple(r['year'] for r in rows) != YEARS:
        raise ValueError('Exactly five forecast years, FY2026-FY2030, are required')
    previous = opening
    for r in rows:
        year = r['year']
        for key, val in r.items():
            if isinstance(val, (int, float)) and not isfinite(val):
                raise ValueError(f'FY{year}: {key} is not finite')
        gaps = {
            'balance sheet': balance_gap(r),
            'reported asset total': r['assets'] - totals(r)[0],
            'reported liability total': r['liabilities'] - totals(r)[1],
            'reported liabilities plus equity': r['liabilities_equity'] - r['liabilities'] - r['equity'],
            'cash flow': r['cash'] - previous['cash'] - r['operating_cf']
                         - r['investing_cf'] - r['financing_cf'],
            'equity roll-forward': r['equity'] - previous['equity']
                                  - r['net_income'] + r['buyback'] + r['dividends'],
            'PP&E roll-forward': r['ppe'] - previous['ppe'] - r['capex']
                                 + r['depreciation'],
            'debt roll-forward': r['debt'] - previous['debt'] + r['repayment'],
            'revolver roll-forward': r['revolver'] - previous['revolver'] - r['revolver_cf'],
            'other assets roll-forward': r['other_assets'] - previous['other_assets']
                                        - r['working_capital'] + r['amortization'] + r['impairment'],
            'customer funds match': r['customer_receivable'] - r['customer_payable'],
            'FCFE link': r['fcfe'] - r['operating_cf'] + r['capex']
                         + r['repayment'] - r['revolver_cf'],
        }
        for name, gap in gaps.items():
            require_zero(year, name, gap)
        if r['cash'] < a['min_cash'] - TOL:
            raise ValueError(f'FY{year}: cash floor shortfall {a["min_cash"] - r["cash"]:,.6f} million')
        if not -TOL <= r['revolver'] <= a['revolver_limit'] + TOL:
            raise ValueError(f'FY{year}: revolver outside available capacity')
        for name in ('ppe', 'debt', 'other_assets', 'customer_receivable'):
            if r[name] < -TOL:
                raise ValueError(f'FY{year}: negative {name}')
        previous = r


def project(assumptions=None, opening=None):
    a = ASSUMPTIONS.copy() if assumptions is None else assumptions.copy()
    first = OPENING.copy() if opening is None else opening.copy()
    validate_inputs(a, first)
    p, rows = first, []
    for year in YEARS:
        r = dict(year=year)
        r['revenue'] = p['revenue'] * (1 + a['growth'])
        r['gross_profit'] = r['revenue'] * a['gross_margin']
        r['cogs'] = r['revenue'] - r['gross_profit']
        r['sga'] = r['gross_profit'] * a['sga_ratio']
        r['product_development'] = r['revenue'] * a['product_development_ratio']
        r['transaction_losses'] = r['revenue'] * a['transaction_loss_ratio']
        r['depreciation'] = p['ppe'] * a['depreciation_ratio']
        r['amortization'], r['impairment'] = a['amortization'], a['impairment']
        r['operating_income'] = (r['gross_profit'] - r['sga'] - r['product_development']
                                 - r['transaction_losses'] - r['amortization'] - r['impairment'])
        r['interest'] = p['debt'] * a['debt_rate'] + p['revolver'] * a['revolver_rate']
        r['pretax'] = r['operating_income'] - r['interest']
        r['tax'] = max(0., r['pretax']) * a['tax_rate']
        r['net_income'] = r['pretax'] - r['tax']
        r['capex'] = r['revenue'] * a['capex_ratio']
        r['working_capital'] = (r['revenue'] - p['revenue']) * a['working_capital_ratio']
        r['customer_receivable'] = p['customer_receivable'] * (1 + a['growth'])
        r['customer_payable'] = r['customer_receivable']
        r['customer_receivable_cf'] = -(r['customer_receivable'] - p['customer_receivable'])
        r['customer_payable_cf'] = r['customer_payable'] - p['customer_payable']
        r['operating_cf'] = (r['net_income'] + r['depreciation'] + r['amortization']
                             + r['impairment'] - r['working_capital']
                             + r['customer_receivable_cf'] + r['customer_payable_cf'])
        r['investing_cf'] = -r['capex']
        r['repayment'] = min(a['repayment'], p['debt'])
        r['debt'] = p['debt'] - r['repayment']
        r['buyback'], r['dividends'] = a['buyback'], a['dividends']
        r['fcfe_before_revolver'] = r['operating_cf'] - r['capex'] - r['repayment']
        r['opening_cash'] = p['cash']
        cash_before = p['cash'] + r['fcfe_before_revolver'] - r['buyback'] - r['dividends']
        if cash_before < a['min_cash']:
            r['revolver_cf'] = min(a['min_cash'] - cash_before,
                                     a['revolver_limit'] - p['revolver'])
        else:
            r['revolver_cf'] = -min(cash_before - a['min_cash'], p['revolver'])
        r['revolver'] = p['revolver'] + r['revolver_cf']
        r['fcfe'] = r['fcfe_before_revolver'] + r['revolver_cf']
        r['financing_cf'] = -r['repayment'] - r['buyback'] - r['dividends'] + r['revolver_cf']
        r['cash_change'] = r['operating_cf'] + r['investing_cf'] + r['financing_cf']
        r['cash'] = p['cash'] + r['cash_change']
        r['ppe'] = p['ppe'] + r['capex'] - r['depreciation']
        r['other_assets'] = p['other_assets'] + r['working_capital'] - r['amortization'] - r['impairment']
        r['investments'], r['other_liabilities'] = p['investments'], p['other_liabilities']
        r['equity'] = p['equity'] + r['net_income'] - r['buyback'] - r['dividends']
        r['inventory'], r['floor'] = 0., 0.
        r['assets'], r['liabilities'] = totals(r)
        r['liabilities_equity'] = r['liabilities'] + r['equity']
        rows.append(r)
        p = r
    check_rows(rows, a, first)
    return rows


def value(rows, a=None, opening=None):
    a = ASSUMPTIONS if a is None else a
    opening = OPENING if opening is None else opening
    validate_inputs(a, opening)
    check_rows(rows, a, opening)
    k, g = a['cost_of_equity'], a['terminal_growth']
    # Lab-specific positive-only convention. Negative FCFE is still in statements.
    pv_fcfe = sum(max(0., r['fcfe']) / (1 + k) ** t for t, r in enumerate(rows, 1))
    last = rows[-1]
    # Lab 09 convention: after 2030, debt is refinanced (no perpetual $250 paydown).
    # Remove the last year's revolver financing too; it cannot grow forever.
    terminal_base = last['fcfe'] + last['repayment'] - last['revolver_cf']
    terminal_allowed = last['fcfe'] > 0 and terminal_base > 0
    terminal = terminal_base * (1 + g) / (k - g) if terminal_allowed else 0.
    pv_terminal = terminal / (1 + k) ** len(rows)
    excess_cash = max(0., opening['cash'] - a['min_cash'])
    equity = pv_fcfe + pv_terminal + excess_cash + opening['investments']
    return dict(pv_fcfe=pv_fcfe, terminal=terminal, pv_terminal=pv_terminal,
                terminal_base=terminal_base, terminal_allowed=terminal_allowed,
                excess_cash=excess_cash, investments=opening['investments'],
                equity=equity, price=equity / a['shares'])


def table(title, keys, rows):
    print('\n' + title + ' (USD millions)')
    print(f'{"Line":<33}' + ''.join(f'{"FY" + str(r["year"]) + "E":>13}' for r in rows))
    for key in keys:
        label = key.replace('_', ' ').title()
        print(f'{label:<33}' + ''.join(f'{r[key]:>13,.2f}' for r in rows))


def report():
    rows = project()
    v = value(rows)
    print('EBAY LAB 10 | Opening/valuation date: 2025-12-31 | FY2026-FY2030')
    print('Source assumptions: lab10_notes.md; implementation judgments: ebay_proforma_model_notes.md')
    print('Marketplace model: no separate inventory/floor-plan financing; customer funds are ring-fenced.')
    table('INCOME STATEMENT', ['revenue', 'cogs', 'gross_profit', 'sga', 'product_development',
          'transaction_losses', 'amortization', 'impairment', 'operating_income',
          'interest', 'pretax', 'tax', 'net_income'], rows)
    print('Depreciation is embedded in the expense ratios above; its schedule appears in cash flow.')
    table('BALANCE SHEET', ['cash', 'investments', 'customer_receivable', 'ppe', 'other_assets',
          'inventory', 'assets', 'debt', 'customer_payable', 'other_liabilities', 'revolver',
          'floor', 'liabilities', 'equity', 'liabilities_equity'], rows)
    table('CASH FLOW AND FCFE', ['net_income', 'depreciation', 'amortization', 'impairment',
          'working_capital', 'customer_receivable_cf', 'customer_payable_cf', 'operating_cf',
          'investing_cf', 'repayment', 'fcfe_before_revolver', 'revolver_cf', 'fcfe',
          'buyback', 'dividends', 'financing_cf', 'cash_change', 'opening_cash', 'cash'], rows)
    print('Working capital, repayment, buyback and dividends are shown as positive cash uses.')
    print('\nCHECK BLOCK (all gaps in USD millions; checked at 0.000001 tolerance)')
    previous = OPENING
    for r in rows:
        gaps = [balance_gap(r), r['cash'] - previous['cash'] - r['operating_cf']
                - r['investing_cf'] - r['financing_cf'],
                r['equity'] - previous['equity'] - r['net_income'] + r['buyback'] + r['dividends']]
        formatted = ', '.join(f'{0. if abs(x) < TOL else x:.6f}' for x in gaps)
        print(f'FY{r["year"]}E: BS / cash / equity gaps = {formatted}; cash floor PASS; revolver PASS')
        if r['revolver_cf'] > TOL:
            print(f'  Draw {r["revolver_cf"]:,.2f}: operations after capex, paydown and distributions '
                  'do not leave the required corporate cash reserve.')
        if r['fcfe'] < 0:
            print('  negative FCFE: excluded from valuation under the lab instruction.')
        previous = r
    print('PP&E, debt, revolver, other assets, customer funds and FCFE links: PASS')
    print('\nDISCOUNTED FCFE VALUATION (USD millions unless stated)')
    for label, key in [('PV of positive forecast FCFE', 'pv_fcfe'),
                       ('Normalized terminal FCFE base', 'terminal_base'),
                       ('Terminal value at end of 2030', 'terminal'), ('PV of terminal value', 'pv_terminal'),
                       ('Opening cash above reserve', 'excess_cash'),
                       ('Investments at carrying-value proxy', 'investments'), ('Equity value', 'equity')]:
        print(f'{label}: {v[key]:,.2f}')
    if not v['terminal_allowed']:
        print('Terminal value excluded: negative/nonpositive cash flow does not establish a '
              'sustainable positive distribution to capitalize; a recovery path is needed.')
    print('No second debt subtraction: FCFE already reflects interest and net borrowing.')
    print('Terminal convention: refinance remaining debt after 2030; no perpetual debt paydown.')
    print(f'Opening shares (millions): {ASSUMPTIONS["shares"]:.0f}')
    print(f'Value per share: ${v["price"]:.2f}')
    if v['equity'] > 0:
        print(f'Share of total equity value after 2030: {100 * v["pv_terminal"] / v["equity"]:.2f}%')
    print('This is a 2025 year-end scenario, not a valuation rolled forward to today.')
    print('\nDATED MARKET COMPARISON (saved quote; not refreshed automatically)')
    print(f'The model says ${v["price"]:.2f}, the market says ${MARKET_PRICE:.2f} '
          f'on {MARKET_DATE}; using 449 million shares for both equity-value comparisons, '
          'what differences in growth, risk or post-2025 developments explain the gap?')
    print(f'Market equity on the common 449m-share basis: {MARKET_PRICE * ASSUMPTIONS["shares"]:,.2f} million; '
          'this is not current reported market capitalization.')
    print(f'Quote source: {MARKET_SOURCE}')
    print('\nFILING SOURCES')
    for year, url in SOURCES.items():
        print(f'{year} 10-K: {url}')


def self_test():
    """Exercise economically different scenarios and the lab's refusal requirement."""
    rows = project()
    value(rows)
    print('PASS: base case balances and values')

    def rejects(name, callback, expected):
        try:
            callback()
        except ValueError as exc:
            if expected not in str(exc):
                raise AssertionError(f'{name}: unexpected refusal: {exc}') from exc
            print(f'PASS: {name} refused ({exc})')
        else:
            raise AssertionError(f'{name}: model failed to refuse')

    broken = deepcopy(rows)
    broken[0]['cash'] = OPENING['cash']
    rejects('typed cash', lambda: check_rows(broken, ASSUMPTIONS, OPENING), 'balance sheet')
    broken = deepcopy(rows)
    broken[0]['operating_cf'] += 100
    rejects('broken cash-flow link', lambda: check_rows(broken, ASSUMPTIONS, OPENING), 'cash flow')
    bad_opening = dict(OPENING, equity=OPENING['equity'] + 1)
    rejects('bad opening balance', lambda: project(opening=bad_opening), 'opening balance sheet')
    stress = dict(ASSUMPTIONS, buyback=10000.)
    rejects('exhausted credit line', lambda: project(stress), 'cash floor shortfall')
    bad_rate = dict(ASSUMPTIONS, terminal_growth=.10)
    rejects('invalid terminal spread', lambda: project(bad_rate), 'terminal growth')
    bad_input = dict(ASSUMPTIONS, growth=float('nan'))
    rejects('NaN input', lambda: project(bad_input), 'finite')
    funded = dict(ASSUMPTIONS, buyback=1150.)
    funded_rows = project(funded)
    if not any(r['revolver_cf'] > TOL for r in funded_rows):
        raise AssertionError('Stress did not exercise revolver draw')
    if not any(r['revolver_cf'] < -TOL for r in funded_rows):
        raise AssertionError('Stress did not exercise revolver repayment')
    print('PASS: revolver draw and subsequent repayment preserve balance and floor')
    losses = dict(ASSUMPTIONS, gross_margin=.10, buyback=0., dividends=0.,
                  repayment=0., revolver_limit=100000.)
    loss_rows = project(losses)
    loss_value = value(loss_rows, losses)
    if not all(r['fcfe_before_revolver'] < 0 for r in loss_rows):
        raise AssertionError('Loss scenario did not lose cash before financing')
    if loss_value['terminal_allowed']:
        raise AssertionError('Negative normalized terminal cash flow was capitalized')
    print('PASS: funded operating losses balance; negative terminal base is not capitalized')
    # Cash-rich loss scenario has genuinely negative FCFE without financing support.
    cash_rich = dict(OPENING, cash=101867., equity=104615.)
    loss_rows = project(losses, cash_rich)
    loss_value = value(loss_rows, losses, cash_rich)
    if not all(r['fcfe'] < 0 for r in loss_rows) or loss_value['pv_fcfe'] != 0:
        raise AssertionError('Negative FCFE exclusion failed')
    print('PASS: negative FCFE retained in statements and excluded from lab valuation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--break-test', action='store_true', help='Deliberately freeze FY2026 cash; must fail')
    parser.add_argument('--output', type=Path, help='Save the same report as UTF-8 text')
    args = parser.parse_args()
    try:
        if args.break_test:
            broken = project()
            broken[0]['cash'] = OPENING['cash']
            value(broken)  # Must refuse before producing a valuation.
            raise AssertionError('Break test incorrectly accepted typed cash')
        elif args.self_test:
            self_test()
        else:
            buffer = StringIO()
            with redirect_stdout(buffer):
                report()
            result = buffer.getvalue()
            print(result, end='')
            if args.output:
                args.output.write_text(result, encoding='utf-8')
    except (ValueError, AssertionError) as exc:
        raise SystemExit(f'MODEL REFUSED: {exc}') from exc


if __name__ == '__main__':
    main()
