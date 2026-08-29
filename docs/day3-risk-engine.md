# RecoverAI Revenue Risk Engine Specification (Day 3)

This document details the deterministic **Revenue Risk Engine** architecture, mathematical scoring rules, priority categorization, **Expected Recoverable Revenue** derivation, and portfolio evaluation metrics across RecoverAI's 25,000-session dataset.

---

## 1. Executive Summary & Core Discovery

The Day 3 Risk Engine answers the central merchant operational question: **"Which customer events represent the highest-value recovery opportunities?"**

```
======================================================================
 RecoverAI Risk Engine Portfolio Summary (25,000 Sessions)
======================================================================
 Total Sessions Analyzed      : 25,000
 Cart Abandonment Events      : 10,501 (42.0% of all sessions)
 Qualified Recovery Candidates: 10,359 (98.6% of abandoned carts)
----------------------------------------------------------------------
 POTENTIAL REVENUE AT RISK    : ₹18,560,150.53 (₹1.85 Crore)
 EXPECTED RECOVERABLE REVENUE : ₹11,630,761.90 (₹1.16 Crore)
 Portfolio Recovery Potential : 62.67%
======================================================================
```

> [!IMPORTANT]
> **Key Revenue Metric Distinction**:
> - **Potential Revenue at Risk**: The gross nominal cart value of all uncompleted checkouts ($₹18.56\text{M}$).
> - **Expected Recoverable Revenue**: The probability-adjusted monetary recovery value ($₹11.63\text{M}$).
>   $$\text{Expected Recoverable Revenue} = \text{cart\_value} \times \left(\frac{\text{purchase\_intent\_score}}{100}\right)$$

---

## 2. Deterministic Risk Scoring Model ($0 \le S_{\text{risk}} \le 100$)

The risk score is a deterministic, multi-factor weighted combination of five behavioral and transactional pillars:

$$S_{\text{risk}} = 0.25 \cdot S_{\text{cart}} + 0.30 \cdot S_{\text{intent}} + 0.20 \cdot S_{\text{history}} + 0.15 \cdot S_{\text{engagement}} + 0.10 \cdot S_{\text{recency}}$$

```
┌─────────────────────────────────────────────────────────────┐
│                 Blended Risk Score (0–100)                  │
├───────────────────┬────────┬────────────────────────────────┤
│ Pillar            │ Weight │ Core Focus                     │
├───────────────────┼────────┼────────────────────────────────┤
│ Cart/Order Value  │  25%   │ Monetary exposure size         │
│ Purchase Intent   │  30%   │ Behavioral intent probability  │
│ Customer History  │  20%   │ Loyalty, CLV & prior purchases │
│ Engagement        │  15%   │ Dwell time & page depth        │
│ Recency Decay     │  10%   │ Timeliness / conversion window │
└───────────────────┴────────┴────────────────────────────────┘
```

---

## 3. Pillar Sub-Score Formulations

### A. Cart / Order Value Score ($S_{\text{cart}} \in [0, 100]$) — Weight: 25%
Scales cart value relative to retail catalog benchmarks ($\text{Benchmark} = ₹3,500$ INR):
$$S_{\text{cart}} = \min\left(\frac{\text{cart\_value}}{3500.0}, 1.0\right) \times 100.0$$

### B. Purchase Intent Score ($S_{\text{intent}} \in [0, 100]$) — Weight: 30%
Directly ingests the Day 2 multi-factor behavioral intent score derived from observable buyer actions.

### C. Customer History Score ($S_{\text{history}} \in [0, 100]$) — Weight: 20%
A repeat customer abandoning a high-value cart scores higher than a first-time visitor with the same cart value:
- **Order Count Factor (45 pts)**: $\min\left(\frac{\text{purchase\_history}}{3.0}, 1.0\right) \times 45.0$
- **Customer Lifetime Value (35 pts)**: $\min\left(\frac{\text{customer\_lifetime\_value}}{4000.0}, 1.0\right) \times 35.0$
- **Loyalty Frequency (20 pts)**: $\min\left(\frac{\text{total\_sessions}}{5.0}, 1.0\right) \times 20.0$

### D. Engagement Score ($S_{\text{engagement}} \in [0, 100]$) — Weight: 15%
Quantifies session depth and checkout consideration:
- **Session Duration (45 pts)**: $\min\left(\frac{\text{session\_duration}}{1500.0}, 1.0\right) \times 45.0$
- **Page Breadth (35 pts)**: $\min\left(\frac{\text{pages\_viewed}}{20.0}, 1.0\right) \times 35.0$
- **Cart Action (20 pts)**: $20.0 \text{ if cart present else } 0.0$

### E. Recency Score ($S_{\text{recency}} \in [0, 100]$) — Weight: 10%
Models the psychological time-decay of buyer intent:
$$S_{\text{recency}} = \begin{cases} 
100.0 & \text{if } t < 1 \text{ hour} \\
80.0  & \text{if } 1 \le t < 6 \text{ hours} \\
60.0  & \text{if } 6 \le t < 24 \text{ hours} \\
30.0  & \text{if } 24 \le t \le 72 \text{ hours (1–3 days)} \\
10.0  & \text{if } t > 72 \text{ hours (>3 days)}
\end{cases}$$

---

## 4. Priority Categorization Tiers

Each event is classified into an operational urgency tier that drives autonomous recovery scheduling (Day 4):

| Priority Tier | Risk Score Range | Abandoned Carts | Share (%) | Potential Revenue at Risk | Expected Recoverable Revenue | Operational SLA |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **CRITICAL** | **80 – 100** | 286 | 2.7% | ₹1,151,943.24 | ₹971,290.23 | Immediate WhatsApp / SMS (<15 min) |
| **HIGH** | **60 – 79** | 2,893 | 27.5% | ₹8,147,009.68 | ₹5,572,091.37 | Expedited Email + Discount (<1 hr) |
| **MEDIUM** | **40 – 59** | 5,696 | 54.2% | ₹8,218,984.00 | ₹4,619,332.88 | Standard Follow-up Reminder (<6 hrs) |
| **LOW** | **0 – 39** | 1,626 | 15.5% | ₹1,042,213.61 | ₹468,047.42 | Passive Retargeting / Digest |

---

## 5. Payment Instrument Recovery Dynamics

| Payment Method | Abandoned Carts | Revenue at Risk (INR) | Expected Recoverable (INR) | Avg Intent Score |
| :--- | :---: | :---: | :---: | :---: |
| **CARD (Credit)** | 1,780 | ₹3,062,237.47 | ₹1,937,313.19 | 60.3 |
| **COD_EMI** | 1,702 | ₹2,963,207.95 | ₹1,865,719.67 | 60.4 |
| **DEBIT_CARD** | 1,676 | ₹2,985,048.86 | ₹1,865,478.67 | 60.7 |
| **NETBANKING** | 1,714 | ₹3,015,919.08 | ₹1,885,429.36 | 60.1 |
| **UPI** | 1,803 | ₹3,152,156.56 | ₹1,962,186.77 | 60.1 |
| **WALLET** | 1,826 | ₹3,381,580.61 | ₹2,114,634.24 | 60.6 |

---

## 6. Top 10 Highest-Value Recovery Opportunities

These represent the top prime candidates for autonomous recovery outreach in Day 4:

| Event ID | Customer ID | Cart Value | Intent Score | Risk Score | Priority Tier | Expected Recoverable |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| `evt_000666` | `cust_05529` | ₹7,735.08 | 85.8 | **86.9** | **CRITICAL** | **₹6,632.83** |
| `evt_014183` | `cust_06163` | ₹7,907.96 | 82.4 | **82.8** | **CRITICAL** | **₹6,515.37** |
| `evt_011293` | `cust_06223` | ₹7,641.28 | 80.8 | **82.4** | **CRITICAL** | **₹6,170.33** |
| `evt_004803` | `cust_08129` | ₹7,268.24 | 82.5 | **84.1** | **CRITICAL** | **₹5,996.30** |
| `evt_021040` | `cust_03586` | ₹7,125.53 | 83.8 | **84.6** | **CRITICAL** | **₹5,972.62** |
| `evt_022363` | `cust_01158` | ₹7,325.04 | 81.3 | **83.7** | **CRITICAL** | **₹5,956.72** |
| `evt_003226` | `cust_06208` | ₹7,871.48 | 75.6 | **80.5** | **CRITICAL** | **₹5,950.84** |
| `evt_017025` | `cust_05505` | ₹6,480.06 | 90.9 | **89.4** | **CRITICAL** | **₹5,889.73** |
| `evt_010425` | `cust_09663` | ₹7,309.80 | 79.8 | **82.3** | **CRITICAL** | **₹5,834.68** |
| `evt_002968` | `cust_07476` | ₹6,810.60 | 84.6 | **84.8** | **CRITICAL** | **₹5,759.04** |

---

## 7. How to Run the Evaluation CLI

To run the risk engine across the entire dataset and generate the updated report:
```bash
python backend/data_pipeline/evaluate_risk.py
```
Outputs the evaluated dataset to `data/processed/recoverai_risk_evaluated.csv`.
