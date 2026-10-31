
# AI Usage Log
## COD Risk Decision Engine

### Purpose

AI tools were used during the development of the COD Risk Decision Engine to assist with code development, debugging, data analysis, financial calculations, and documentation.

AI-generated suggestions were reviewed and tested against the dataset and project requirements. Final decisions about business rules and implementation were made after evaluating their correctness.
---

### Example 1: Handling Inconsistent Customer History

Area: Decision engine and customer-history validation

**AI suggestion / initial approach:**

An initial approach grouped inconsistent customer-history records with records having missing customer information and sent both categories for WhatsApp confirmation.

**Problem identified:**

Some records had `customer_prior_rto` greater than `customer_prior_orders`. This is logically inconsistent customer-history data. Asking the customer to confirm the order would not resolve the underlying data inconsistency.

**Correction made:**

A separate rule was introduced to identify these records and assign them to `hold/cancel`, which maps to `HOLD_FOR_MANUAL_REVIEW`.

**Final decision:**

Inconsistent history requires human review rather than an ordinary WhatsApp confirmation.
---

### Example 2: Manual Review Versus Automatic Cancellation

**Area:** Decision workflow

**AI suggestion / initial approach:**

The initial workflow needed a clearer distinction between holding an order for review and cancelling it. A manual-review state could otherwise be misinterpreted as an actual cancellation.

**Problem identified:**

Automatically treating every high-risk or manually reviewed order as cancelled could result in losing genuine customers and incorrectly calculating lost gross margin.

Correction made:

The workflow was explicitly mapped as follows:

- `ship as-is` → `SHIP`
- `nudge to prepaid` → `WAITING_FOR_CUSTOMER`
- `WhatsApp confirmation` → `WAITING_FOR_CUSTOMER`
- `hold/cancel` → `HOLD_FOR_MANUAL_REVIEW`

Actual cancellation was kept separate from manual review.

**Final decision:**

The current engine does not automatically cancel orders. Actual cancellation and lost gross margin cannot be measured until human review outcomes are recorded.
---

### Example 3: Separating Historical Outcomes from Simulated Interactions

**Area:** Dashboard and financial reporting

**AI suggestion / initial approach:**

The dashboard needed to combine decision-engine outputs, historical order outcomes, and WhatsApp interaction results.

**Problem identified:**

Combining these populations without clear labels could make simulated customer responses appear to be real customer interactions. Similarly, orders without final outcomes or historical RTO comparisons could be misinterpreted.

**Correction made:**

The dashboard was separated into distinct sections:

- Initial decision distribution.
- Final workflow action distribution.
- Simulated WhatsApp interaction results.
- Historical RTO performance using only `DELIVERED` and `RTO` outcomes.
- Hypothetical prepaid-conversion financial scenario.

The dashboard also identifies the historical reporting period as 1 April to 30 September 2026.

**Final decision:**

Simulated interactions are explicitly labelled as simulations. Historical financial figures and hypothetical scenario estimates are presented separately.
---

### AI Usage and Human Validation

AI assistance was used for:

- Understanding and analysing the historical dataset.
- Developing and debugging Python code.
- Structuring configurable decision rules.
- Building the WhatsApp mock workflow.
- Developing the Streamlit dashboard.
- Reviewing financial calculations and backtesting results.
- Preparing project documentation.

Human validation included:

- Running the Python scripts and checking their outputs.
- Comparing decision-engine results with backtesting predictions.
- Checking financial calculations against the stated assumptions.
- Reviewing the distinction between historical results and hypothetical estimates.
- Ensuring that manual review was not incorrectly treated as cancellation.

**Conclusion:**

AI was used as a development assistant, not as an unquestioned source of truth. Suggestions were reviewed, tested, and corrected where necessary. Business decisions and final implementation logic remained subject to human validation.
