# Lab 11 — eBay pro-forma sensitivity

> DRAFT: Calculated eBay results are actual model output. All wording marked **SAMPLE** is suggested wording, not a record of a conversation or a statement of the student's own interpretation. Replace samples with the actual exchanges and your own conclusions before submission. Partner company/results and GitHub URLs have not been supplied; do not treat illustrative numbers as evidence.

Question: Which assumptions drive my company's forecast and value, and what explains their effects?

## Base and comparison

Lab 10 model: `ebay_proforma.py` (preserved). Baseline inputs: `lab11_base_inputs.json`. Visible baseline output: `lab11_base_output.txt`. Initial accounting checks and model self-tests passed.

Compare FY2030 operating profit and FCFE in USD millions, and value per share in USD where the existing valuation is usable. The valuation date remains December 31, 2025; it is not a current market valuation.

## Selected independent inputs

Apply each scenario's constant annual input to FY2026–FY2030. Change only one independent input at a time; reset all others to the saved base and recalculate the linked statements.

| Independent input | Lower | Base | Higher | Units | Range label |
|---|---:|---:|---:|---|---|
| Annual revenue growth (`growth`) | 2% | 4% | 6% | Annual percent growth | Judgment informed by history |
| Gross margin (`gross_margin`) | 70.45% | 7931 / 11100 = approximately 71.45045045% | 72.45% | Gross profit as percent of revenue | Judgment stress range |

Revenue growth changes are -2 and +2 percentage points from base. Gross-margin endpoints are the student's exact specified percentages; shifts from the unrounded model base are approximately -1.00045045 and +0.99954955 percentage points. Preserve the exact model base rather than rounding it to 71.45%.

Student's revenue-growth rationale: It tests how the size of eBay's business affects profits, reinvestment, and cash flow. Historical revenue growth was approximately 3.24% in 2023, 1.69% in 2024, and 7.95% in 2025. A 2%–6% range covers slower and stronger growth without assuming the strongest recent year repeats throughout the forecast. Label: judgment informed by history.

Student's gross-margin rationale: It tests how much revenue remains after the cost of providing eBay's services. Historical margins were approximately 71.98%, 71.99%, and 71.45%. Testing approximately one percentage point above and below the base deliberately extends beyond that recent variation to examine sustained cost pressure or improvement. Label: judgment stress range, not company guidance.

Historical figures and filing references are carried forward from Lab 10, not newly verified for this sensitivity exercise: [2024 filing](https://www.sec.gov/Archives/edgar/data/1065088/000106508825000037/ebay-20241231.htm), [2025 filing](https://www.sec.gov/Archives/edgar/data/1065088/000106508826000027/ebay-20251231.htm).

## Locked Changed-Input Record

Before any changed-input run, close AI, save your own prediction with a timestamp or Git commit, and show the prediction and ranges to your partner.

- Timestamp or Git commit: 9/29/2026 5:00 P.M.
- One selected input, old → new, including units and affected years: Annual revenue growth increases 4% -> 6% for FY2026-FY2030.
- Expected output direction and rough size: Compared to the base case, I predict that 2030 operating profit will increase by about 8%, 2030 FCFE will increase by about 12%, and value per share (VPS) will increase by about 10%.
- Why (input → statement → output): Faster revenue growth should compound over the five years. I also expect higher revenue to increase operating profit. More capital spending will absorb some cash, but I think FCFE will rise overall. And higher FCFE should increase VPS.
- **🟨 SAMPLE — Partner's units and one-input-at-a-time check:** “We checked that 4% to 6% is a 2-percentage-point increase, applied to each year from 2026–2030. Only revenue growth changes in this scenario; gross margin and all other independent inputs stay at base.” Replace with your partner's name and actual check/corrections.

## After the changed-input run — actual results and draft explanation

- Actual result and signed difference from base: Revenue growth 4% → 6% in FY2026–FY2030, all other independent assumptions at base. FY2030 operating profit: $2,770.165056m → $3,049.368862m, change +$279.203806m (+10.08%). FY2030 FCFE: $1,715.032047m → $1,898.466872m, change +$183.434825m (+10.70%). Value/share: $60.241915 → $64.476919, change +$4.235005 (+7.03%). Actual percentage changes minus predicted changes: operating profit +2.08 percentage points; FCFE -1.30 percentage points; value/share -2.97 percentage points. Differences use unrounded model values.
- **SAMPLE interpretation — Explanation of prediction error:** “I underestimated operating-profit growth: it rose 10.08%, versus my 8% prediction. The growth change compounds across five years, and fixed amortization makes operating profit rise slightly faster than revenue. I overestimated FCFE growth: it rose 10.70%, versus my 12% prediction. Higher capital spending and working-capital investment absorb some additional operating cash flow. I also overestimated the value increase: it rose 7.03%, versus my 10% prediction. Value depends on all forecast years and terminal cash flow, not just final-year FCFE, and the cash and investment amounts added to value do not increase in this scenario.”
- **SAMPLE interpretation — Valuation conclusion/research priority:** “This does not reverse my model's conclusion relative to the saved September 24, 2026 quote of $107.83: even the 6% growth case produces $64.48 per share. This comparison uses a December 31, 2025 valuation and a later saved quote, so it is not an updated valuation. My research priority would be checking whether sustained revenue growth above my base is supported and whether the terminal and other valuation assumptions explain the remaining gap.”

## Partner exchange notes — pending actual exchanges

### 🟨 FILL IN — Partner exchange 1: before running changes

Status: Student reports this exchange is complete. Record the actual discussion below; its details have not yet been supplied here.

- **SAMPLE — Question my partner asked me:** “Why did you choose 2%–6% growth rather than repeat the strongest recent year?”
- **SAMPLE — My response:** “Recent annual growth ranged from about 1.69% to 7.95%. My range tests slower and stronger growth without assuming the strongest year repeats throughout the forecast. It is judgment informed by history.”
- **SAMPLE — Gap or correction identified:** “We clarified that the change is 2 percentage points, not a 2% relative increase, and applies to all five forecast years.”
- **SAMPLE — My check/question on my partner's prediction and ranges:** “Your proposed input change affects operating profit and then cash flow through the linked statements. What historical evidence supports your endpoints? Are the units clear, and are you holding the other independent inputs fixed?” Replace the general description with their actual input and mechanism.
- **SAMPLE — Partner's response:** “My endpoints reflect historical variation and a judgment about future conditions. I will change only the selected input and let the linked statements recalculate.” Replace with their actual explanation.

### 🟨 FILL IN — Partner exchange 2: check actual results

- **Result prepared to show my partner:** Annual revenue growth 4% → 6% for FY2026–FY2030. FY2030 operating profit increases from $2,770.165056 million to $3,049.368862 million: +$279.203806 million. Only `growth` changes in the independent input set; gross margin and every other independent input remain at base. Full evidence: [sensitivity output](lab11_sensitivity_output.md) and [full-precision inputs/statements](lab11_sensitivity_details.json).
- **SAMPLE — Partner's check/question and my response:** “My partner recomputed $3,049.37m minus $2,770.17m as +$279.20m and checked that only `growth` changed. They asked why capital spending also increased. I explained that its ratio stayed at base, but the dollar amount increased with revenue. A linked dollar amount changing is different from changing another independent assumption.”
- **SAMPLE — What I checked on my partner's analysis:** “I compared the base and changed input lists, checked final-year FCFE, and traced the selected input through profit and reinvestment.” Add the actual company, input, and scenario; these are not known yet.
- **SAMPLE ONLY — Difference I recomputed:** “For illustration, changed FCFE of $550 million minus base FCFE of $500 million equals +$50 million, or +10%.” These are invented teaching numbers, not your partner's results. Replace all three amounts with their actual figures.
- **SAMPLE — Other independent inputs stayed at base:** “I compared the full assumption sets and confirmed that only the selected input differed. I allowed calculated statement amounts to change.” Record what you actually inspected.
- **SAMPLE — My question/correction and partner's response:** “I asked whether their change was a dollar change or a percentage change. They clarified the units and showed the changed result minus the base result.” Replace with the actual exchange.

### 🟨 FILL IN — Partner exchange 3: explain the main driver

- **SAMPLE — Causal link I explained using actual results:** “Raising growth from 4% to 6% increases 2030 revenue from $13,504.85m to $14,854.30m. Expenses and reinvestment also increase, but operating profit rises by $279.20m and FCFE rises by $183.43m using unrounded results.”
- **SAMPLE — Partner's question about whether the chosen ranges affect the ranking:** “Could growth have the bigger effect partly because of the range you selected?”
- **SAMPLE — My response:** “Yes. Growth spans 2%–6%, while gross margin spans 70.45%–72.45%. The ranking applies over these ranges; different endpoints could change it.”
- **SAMPLE — Partner's summary of my conclusion:** “Revenue growth produces the larger span for all three outputs over your tested ranges, but that does not prove it is always the most important input.”
- **SAMPLE — My question and summary of my partner's main driver:** “Does the same input produce the largest span for operating profit and cash flow? Your explanation suggests reinvestment can change the cash-flow ranking.” Replace this with their actual driver, results, and conclusion.
- **SAMPLE — Why our companies may have different main drivers:** “Different cost structures and reinvestment needs can make the same revenue change affect cash flow differently. We should compare these mechanisms and our chosen ranges rather than rank our companies by raw dollar changes.” Add a concrete contrast supported by your partner's model.

## Results and sample interpretation

All six lower/base/higher runs are complete. Each usable run passes accounting checks; the final restored base matches initial inputs and all statement outputs within 0.000001 absolute tolerance. See [visible sensitivity results and statement traces](lab11_sensitivity_output.md) and [full-precision evidence](lab11_sensitivity_details.json). Lab 10 files remain unchanged.

For partner exchange 2, compare the initial base with the annual-revenue-growth higher case. FY2030 revenue changes from $13,504.847217m to $14,854.303911m; operating profit from $2,770.165056m to $3,049.368862m; net income from $2,032.260045m to $2,255.623089m; capital spending from $638.742774m to $702.568428m; working-capital investment from $5.194172m to $8.408097m. These are calculated statement amounts, not additional independent input changes. Use the full statement traces to explain the links in your own words.

Actual calculated spans:

| Output | Revenue-growth span | Gross-margin span |
|---|---:|---:|
| FY2030 operating profit (USD millions) | 537.74 | 147.77 |
| FY2030 FCFE (USD millions) | 354.28 | 118.21 |
| Value per share (USD) | 8.20 | 3.15 |

**SAMPLE interpretation:** “Annual revenue growth is the larger driver for all three outputs over these ranges. Its effects compound across five years and change both earnings and reinvestment. Gross margin also affects profit, but some additional gross profit goes to SG&A because the model holds SG&A as a percentage of gross profit. These results depend on both the chosen ranges and the model's relationships.”

**SAMPLE reflection:** “The result that surprised me was value per share increasing only 7.03% when final-year FCFE increased 10.70%. I expected a closer match, but value includes cash flows from multiple years, terminal cash flow, and fixed opening cash and investments.” Replace with what actually surprised you.

## Learn on your own — sample answers to review

1. What is one-at-a-time sensitivity?

   **SAMPLE:** Change one independent assumption, hold the others at base, and rerun the entire linked model. Compare the outputs with base to isolate that input's effect within the model.

2. How does the chosen input range affect the ranking?

   **SAMPLE:** A wider range can produce a bigger output span. The ranking therefore describes the inputs over the tested ranges, not their inherent importance under every possible scenario.

3. Why is a sensitivity table not a forecast probability?

   **SAMPLE:** The scenarios show what the model produces if an input takes a specified value. They do not assign likelihoods to those values, and testing inputs separately does not capture all the ways inputs could move together.

## Checkout — actual GitHub links still needed

Upload the files to your actual course repository, then copy each file's GitHub URL here. No repository URL has been supplied, so links cannot be completed accurately yet.

- Notes: `https://github.com/YOUR-USERNAME/YOUR-REPOSITORY/blob/YOUR-BRANCH/lab11_notes.md`
- Script: `https://github.com/YOUR-USERNAME/YOUR-REPOSITORY/blob/YOUR-BRANCH/lab11_sensitivity.py`
- Visible results: `https://github.com/YOUR-USERNAME/YOUR-REPOSITORY/blob/YOUR-BRANCH/lab11_sensitivity_output.md`
- Also include `lab11_base_model.py` and `lab11_base_inputs.json`, which the script requires, and `lab11_sensitivity_details.json` for full-precision evidence.

The URLs above are templates, not working submission links.
