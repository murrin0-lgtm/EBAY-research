"""eBay Lab 11. Default: preparation check only; no changed scenarios.

After saving your prediction and completing the partner check:
    py lab11_sensitivity.py --run
Outputs: lab11_sensitivity_output.md and lab11_sensitivity_details.json.
Lab 10 files are read only. Standard library only.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path

import lab11_base_model as model

ROOT = Path(__file__).resolve().parent
RANGES = {'growth': (0.02, 0.06), 'gross_margin': (0.7045, 0.7245)}
LABELS = {'growth': 'Annual revenue growth', 'gross_margin': 'Gross margin'}
METRICS = ('operating_income', 'fcfe', 'price')


def load_base():
    base = json.loads((ROOT / 'lab11_base_inputs.json').read_text(encoding='utf-8'))
    if tuple(base['years']) != model.YEARS:
        raise ValueError('Saved forecast years differ from model years')
    if base['assumptions'] != model.ASSUMPTIONS or base['opening'] != model.OPENING:
        raise ValueError('Saved inputs differ from the preserved model; investigate before running')
    return base


def run_case(base, driver=None, value=None):
    a, opening = deepcopy(base['assumptions']), deepcopy(base['opening'])
    if driver is not None:
        a[driver] = value
    changed = [k for k in a if a[k] != base['assumptions'][k]]
    expected = [] if driver is None or value == base['assumptions'][driver] else [driver]
    if changed != expected:
        raise AssertionError('More than the selected independent input changed')
    result = dict(inputs=deepcopy(a), opening=deepcopy(opening), changed_inputs=changed)
    try:
        rows = model.project(a, opening)
        model.check_rows(rows, a, opening)
    except ValueError as exc:
        return dict(result, valid=False, error=str(exc))
    result.update(valid=True, rows=rows, checks='PASS: all linked accounting checks',
                  operating_income=rows[-1]['operating_income'], fcfe=rows[-1]['fcfe'],
                  price=None, valuation_limitation=None)
    # The old model excludes negative FCFE from its valuation. Do not use that
    # convention for sensitivity runs with negative cash flow; retain all rows.
    if any(r['fcfe'] < 0 for r in rows):
        result['valuation_limitation'] = 'Negative forecast FCFE: existing positive-only valuation is unavailable; signed cash flows retained.'
    else:
        valuation = model.value(rows, a, opening)
        if not valuation['terminal_allowed']:
            result['valuation_limitation'] = 'No supported positive terminal cash flow; value unavailable.'
        else:
            result.update(price=valuation['price'], valuation=valuation)
    return result


def same_results(first, last):
    if first['inputs'] != last['inputs'] or first['opening'] != last['opening']:
        return False
    if not first['valid'] or not last['valid']:
        return False
    for a, b in zip(first['rows'], last['rows']):
        if a.keys() != b.keys() or any(abs(a[k] - b[k]) > model.TOL for k in a):
            return False
    for key in METRICS:
        a, b = first[key], last[key]
        if (a is None) != (b is None) or (a is not None and abs(a - b) > model.TOL):
            return False
    return True


def fmt(value, signed=False):
    if value is None:
        return 'Unavailable'
    return format(value, '+,.2f' if signed else ',.2f')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Run scenarios after your locked prediction and partner check')
    args = parser.parse_args()
    base = load_base()
    if not args.run:
        print('PREPARATION CHECK PASS: saved inputs match the preserved Lab 11 base model.')
        for driver, (low, high) in RANGES.items():
            print(f'{LABELS[driver]}: {low:.8%} / {base["assumptions"][driver]:.8%} / {high:.8%}; FY2026-FY2030')
        print('No forecasts or changed scenarios run. After the locked prediction and partner check: py lab11_sensitivity.py --run')
        return

    original = deepcopy(base)
    first = run_case(base)
    if not first['valid']:
        raise ValueError('Initial base failed: ' + first['error'])
    results = {}
    lines = ['# eBay Lab 11 sensitivity results', '',
             'All inputs apply annually to FY2026-FY2030. Final-year outputs are FY2030.',
             'Operating profit and FCFE: USD millions. Value: USD/share, valuation date December 31, 2025.',
             'Values use existing Lab 10 valuation assumptions, including debt refinancing after 2030 and investments at carrying value.',
             'Each scenario starts from an independent copy of saved base inputs. Signed changes = scenario minus initial base.', '',
             '| Driver | Case | Input (%) | OP | Change OP | FCFE | Change FCFE | Value/share | Change value | Checks |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for driver, (low, high) in RANGES.items():
        results[driver] = {}
        for label, number in [('lower', low), ('base', base['assumptions'][driver]), ('higher', high)]:
            case = run_case(base, driver, number)
            results[driver][label] = case
            if not case['valid']:
                lines.append(f'| {LABELS[driver]} | {label} | {number * 100:.8f} | — | — | — | — | — | — | INVALID: {case["error"]} |')
                continue
            if label == 'base' and not same_results(first, case):
                raise AssertionError('Scenario base did not reproduce initial base')
            case['changes'] = {key: case[key] - first[key] if case[key] is not None and first[key] is not None else None for key in METRICS}
            cells = []
            for key in METRICS:
                cells.extend([fmt(case[key]), fmt(case['changes'][key], True)])
            lines.append(f'| {LABELS[driver]} | {label} | {number * 100:.8f} | ' + ' | '.join(cells) + ' | PASS |')

    spans = {}
    lines += ['', '## Output spans over these ranges', '',
              'Spans are maximum minus minimum across usable lower/base/higher outputs. Invalid runs are excluded; incomplete ranges are not ranked.', '',
              '| Driver | OP span (USD m) | FCFE span (USD m) | Value span (USD/share) | Valid counts OP/FCFE/value |',
              '|---|---:|---:|---:|---|']
    for driver, cases in results.items():
        spans[driver] = {}
        counts = []
        for key in METRICS:
            values = [c[key] for c in cases.values() if c['valid'] and c[key] is not None]
            spans[driver][key] = max(values) - min(values) if len(values) >= 2 else None
            counts.append(str(len(values)) + '/3')
        lines.append('| ' + LABELS[driver] + ' | ' + ' | '.join(fmt(spans[driver][k]) for k in METRICS) + ' | ' + ', '.join(counts) + ' |')

    restored = run_case(base)
    restored_ok = same_results(first, restored) and base == original
    if not restored_ok:
        raise AssertionError('Restored base does not match initial base')
    lines += ['', '## Restored base', '',
              'PASS: identical independent inputs and all statement values and outputs within absolute tolerance 0.000001 (USD millions for statements; USD/share for price).',
              f'Restored FY2030 OP: {fmt(restored["operating_income"])}; FCFE: {fmt(restored["fcfe"])}; value/share: {fmt(restored["price"])}.',
              '', '## Accounting checks and statement traces', '',
              'Every usable run passes the preserved model checks for balance sheet, cash flow, equity, PP&E, debt, revolver, other assets, customer funds, FCFE, and cash floor. Full-precision inputs and all statement rows are saved in lab11_sensitivity_details.json.']
    traces = [('Initial base', first)] + [(f'{LABELS[d]} / {label}', c) for d, cases in results.items() for label, c in cases.items()] + [('Restored base', restored)]
    for name, case in traces:
        lines += ['', f'### {name}', '', 'Changed independent inputs: ' + (', '.join(case['changed_inputs']) or 'none')]
        if not case['valid']:
            lines += ['INVALID: ' + case['error']]
            continue
        lines += [case['checks']]
        if case['valuation_limitation']:
            lines += [case['valuation_limitation']]
        lines += ['', '| Statement line (USD millions) | ' + ' | '.join(str(r['year']) for r in case['rows']) + ' |',
                  '|---|' + '---:|' * len(case['rows'])]
        for key in case['rows'][0]:
            if key != 'year':
                lines.append('| ' + key + ' | ' + ' | '.join(fmt(r[key]) for r in case['rows']) + ' |')
        lines += ['', 'Annual balance-sheet gaps (USD millions): ' + ', '.join(f'{r["year"]}: {model.balance_gap(r):.8f}' for r in case['rows'])]
    lines += ['', 'Student interpretation, locked-prediction reconciliation, and actual partner feedback belong in lab11_notes.md.']
    payload = dict(base_before=first, scenarios=results, spans=spans, base_after=restored, restored_base_pass=restored_ok)
    (ROOT / 'lab11_sensitivity_details.json').write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (ROOT / 'lab11_sensitivity_output.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[:lines.index('## Accounting checks and statement traces')]))
    print('Saved lab11_sensitivity_output.md and lab11_sensitivity_details.json')


if __name__ == '__main__':
    main()
