
# COD Risk Decision Engine

A configurable, rule-based decision-support system for identifying risky Cash-on-Delivery (COD) orders, managing customer confirmation workflows, analysing historical Return-to-Origin (RTO) patterns, and estimating potential financial impact.

## 1. Problem Statement

Cash-on-Delivery orders can result in Return-to-Origin (RTO) when customers refuse delivery or are unavailable. RTO creates additional shipping, return, packaging, and potential product-damage costs.

The objective of this project is to help a D2C business make more informed COD decisions while balancing operational risk and customer experience.

## 2. Key Features

- **Rule-based decision engine:** Assigns each order one of four recommendations.
- **Configurable thresholds:** Business rules can be modified through `config.json`.
- **Customer validation:** Checks phone numbers, pincodes, and customer-history consistency.
- **WhatsApp mock workflow:** Simulates YES, NO, invalid responses, and 24-hour timeouts.
- **Historical analysis:** Evaluates RTO patterns across customer and order characteristics.
- **Chronological backtesting:** Compares decision groups across training and test periods.
- **Financial analysis:** Calculates historical RTO costs and delivered gross margin.
- **Interactive dashboard:** Displays decision distributions, historical performance, and hypothetical prepaid-conversion scenarios.

## 3. Decision Outcomes

| Decision | Description |
|---|---|
| Ship as-is | Order proceeds without additional confirmation. |
| Nudge to prepaid | Customer is offered a prepaid payment option. |
| WhatsApp confirmation | Customer confirmation is requested. |
| Hold for manual review | Order requires human review before proceeding. |

The system does not automatically cancel orders.

## 4. Technology Stack

- Python
- Pandas
- Streamlit
- JSON
- Matplotlib / Streamlit charting

## 5. Project Structure

```text
COD-Risk-Decision-Engine/
│
├── data/
│   └── orders_sample.csv
│
├── config.json
├── data_analysis.py
├── feature_analysis.py
├── advanced_analysis.py
├── decision_engine.py
├── whatsapp_mock.py
├── backtest.py
├── backtest_v2.py
├── dashboard.py
│
├── decision_log.csv
├── backtest_v2_training.csv
├── backtest_v2_testing.csv
├── backtest_v2_decision_check.csv
├── backtest_v2_test_predictions.csv
├── backtest_v2_test_financial_summary.csv
│
├── AI_USAGE_LOG.md
├── README.md
└── COD_Risk_Decision_Founder_Memo.pdf
```

*Adjust the structure above to match the files and folders actually present in your repository.*

## 6. Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd COD-Risk-Decision-Engine
```

Install dependencies:

```bash
pip install pandas streamlit matplotlib
```

## 7. Execution

Run the decision engine:

```bash
python decision_engine.py
```

Run the backtesting analysis:

```bash
python backtest_v2.py
```

Run the WhatsApp mock workflow:

```bash
python whatsapp_mock.py
```

Launch the dashboard:

```bash
streamlit run dashboard.py
```

**Important execution order:** Run the decision engine before the WhatsApp mock workflow because the engine regenerates the decision log and resets simulated interaction results.

## 8. Historical Dataset and Findings

The dataset covers 1 April 2026 to 30 September 2026.

| Metric | Result |
|---|---:|
| Total decision records | 1,988 |
| Orders with final outcomes | 1,987 |
| Delivered orders | 1,422 |
| RTO orders | 565 |
| Historical RTO rate | 28.43% |
| Estimated RTO cost per order | ₹169.40 |
| Historical RTO cost | ₹95,711 |

Historical evaluation includes only orders with `DELIVERED` or `RTO` outcomes.

## 9. Financial Scenario

The dashboard includes a configurable hypothetical prepaid-conversion scenario.

At the default assumptions:

- Eligible orders: 548
- Assumed prepaid conversion rate: 20%
- Assumed prepaid RTO rate: 4%
- Discount per converted order: ₹20
- Estimated net financial impact: ₹22,294.34

This is a scenario estimate, not measured savings or guaranteed business performance.

## 10. Important Limitations

- Historical comparisons do not establish that the decision engine caused a reduction in RTO.
- Decision rules were developed after examining the historical dataset.
- WhatsApp interactions are simulated; no real messages are sent.
- Prepaid conversion and prepaid RTO rates are assumptions.
- The system does not automatically cancel orders.
- Actual lost gross margin from cancellations cannot be calculated without recorded cancellation outcomes.
- Payment gateway fees, WhatsApp costs, and other operational expenses are not included in the financial scenario.

## 11. Documentation

- `COD_Risk_Decision_Founder_Memo.pdf` — Business findings, financial opportunity, risks, and proposed next steps.
- `AI_USAGE_LOG.md` — AI assistance, identified weaknesses, corrections, and human validation.

## 12. Disclaimer

This project is a decision-support prototype developed for an assignment. It is not a production-ready order-management or automated fraud-detection system.
