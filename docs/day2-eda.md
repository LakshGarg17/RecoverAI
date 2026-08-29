# RecoverAI Exploratory Data Analysis & Transformation Spec (Day 2)

This document details the exploratory findings from the 25,000-session Indian e-commerce dataset, formalizes the domain definitions for **Potential Revenue at Risk**, details the **Purchase Intent Score** algorithm, and documents data cleaning and imputation strategies.

---

## 1. Executive Summary & Core Metrics

```
============================================================
 RecoverAI Key Performance & Risk Indicators
============================================================
 Total Sessions Analyzed      : 25,000
 Unique Customers             : 8,442
 Repeat Customers             : 6,918 (81.9%)
 Cart Creation Events         : 16,117 (64.5% of sessions)
 Completed Purchases          : 5,616 (22.5% of sessions)
 Abandoned Carts              : 10,501 (65.2% of created carts)
------------------------------------------------------------
 Total Completed Revenue      : ₹10,116,169.06
 Average Order Value (AOV)    : ₹1,801.31
 POTENTIAL REVENUE AT RISK    : ₹18,560,150.53
 Avg At-Risk Value per Cart   : ₹1,767.47
============================================================
```

> [!IMPORTANT]
> **Core Discovery**: Over **₹1.85 Crore (₹18.56M INR)** sits in abandoned carts across 10,501 sessions—representing **183% of the actual completed revenue (₹1.01 Crore)**. Recovering even a 10–15% fraction of these high-intent dropoffs represents an immense revenue unlock for online merchants.

---

## 2. Customer Behavior & Segmentation

- **Unique Customer Base**: 8,442 distinct customers generated 25,000 sessions.
- **Repeat Engagement**: 6,918 customers (81.9%) visited the store more than once, with an average of 2.96 sessions per customer.
- **Purchasing Distribution**:
  - 4,188 customers completed at least 1 purchase.
  - 1,093 customers completed 2 or more purchases.
  - 4,254 customers exhibited interest (browsing/carting) but have not yet converted.
- **Spending Distribution**:
  - Mean Customer Lifetime Value (CLV) among purchasing customers: **₹2,415.51**
  - Maximum Customer Lifetime Value: **₹11,842.30**
  - Average Order Value (AOV): **₹1,801.31** (Median: ₹1,610.15)

---

## 3. Checkout Funnel & Engagement Dynamics

The shopping funnel exhibits three distinct behavioral cohorts:

| Cohort | Session Count | Share of Total | Avg Pages Viewed | Avg Duration (sec) | Median Duration |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Completed Purchases** | 5,616 | 22.5% | 14.8 pages | 1,072 sec (~17.9 min) | 1,078 sec |
| **Abandoned Carts** | 10,501 | 42.0% | 13.6 pages | 985 sec (~16.4 min) | 987 sec |
| **Browse Only (No Cart)** | 8,883 | 35.5% | 9.8 pages | 699 sec (~11.6 min) | 688 sec |

### Key Insight:
Users who abandon carts exhibit high engagement (13.6 pages viewed, 16.4 minutes on site)—almost identical to converting users (14.8 pages, 17.9 minutes). They are **not casual bounce visitors**; they invested significant consideration before abandoning at checkout.

---

## 4. Payment Instrument Breakdown

Transactions and checkout sessions are evenly distributed across the 6 primary Indian payment modalities:

| Code | Canonical Method | Sessions | Share (%) | Completed Purchases | Conversion Rate (%) | Revenue Completed (INR) | Potential Revenue at Risk (INR) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `0` | **UPI** | 4,227 | 16.9% | 954 | 22.6% | ₹1,714,892.40 | ₹3,142,019.12 |
| `1` | **CARD (Credit)** | 4,281 | 17.1% | 967 | 22.6% | ₹1,745,210.85 | ₹3,178,450.20 |
| `2` | **DEBIT_CARD** | 4,051 | 16.2% | 903 | 22.3% | ₹1,623,780.14 | ₹3,010,219.45 |
| `3` | **NETBANKING** | 4,140 | 16.6% | 928 | 22.4% | ₹1,667,540.32 | ₹3,074,120.80 |
| `4` | **WALLET** | 4,229 | 16.9% | 951 | 22.5% | ₹1,712,015.60 | ₹3,139,812.18 |
| `5` | **COD_EMI** | 4,072 | 16.3% | 913 | 22.4% | ₹1,652,729.75 | ₹3,015,528.78 |

---

## 5. Formal Definition: Potential Revenue at Risk

Because this dataset captures pre-payment cart additions and checkout dropoffs alongside completed transactions, we establish an explicit domain definition for at-risk value:

$$\text{Potential Revenue at Risk} = \begin{cases} \max(0, (\text{unit\_price} \times \text{quantity}) - \text{discount\_amount}) & \text{if } \text{added\_to\_cart} = 1 \text{ and } \text{purchased} = 0 \\ 0.0 & \text{otherwise} \end{cases}$$

### Strict Terminology Rules:
- **Mandatory Label**: Always termed **"Potential Revenue at Risk"** in all code, API responses, analytics tables, and UI cards.
- **Prohibited Terminology**: Never refer to this as "Lost Revenue" or "Actual Revenue" since checkout intent is probabilistic and not guaranteed without autonomous intervention.

---

## 6. Purchase Intent Scoring Model (0 – 100)

To prioritize high-value recovery interventions, RecoverAI computes a multi-factor **Purchase Intent Score** $S \in [0, 100]$ composed of three behavioral pillars:

$$S = \min\left(100.0, \; S_{\text{engagement}} + S_{\text{cart}} + S_{\text{customer}}\right)$$

### 1. Engagement Sub-Score ($0 \le S_{\text{engagement}} \le 30$)
Rewards active session research and dwell time:
- **Page Breadth (15 pts)**: $\min\left(\frac{\text{pages\_viewed}}{20}, 1.0\right) \times 15.0$
- **Session Duration (15 pts)**: $\min\left(\frac{\text{time\_on\_site\_sec}}{1500}, 1.0\right) \times 15.0$

### 2. Action & Cart Sub-Score ($0 \le S_{\text{cart}} \le 35$)
Rewards tangible checkout commitment:
- **Add-to-Cart Action (25 pts)**: $25.0 \text{ if } \text{added\_to\_cart} = 1 \text{ else } 0.0$
- **Cart Monetary Intensity (10 pts)**: $\min\left(\frac{\text{cart\_value}}{3000}, 1.0\right) \times 10.0$ (if cart created)

### 3. Customer Profile & Loyalty Sub-Score ($0 \le S_{\text{customer}} \le 35$)
Accounts for merchant trust and historical propensity:
- **Session Frequency (10 pts)**: $\min\left(\frac{\text{total\_sessions}}{5}, 1.0\right) \times 10.0$
- **Purchase History (15 pts)**: $\min\left(\frac{\text{successful\_purchases}}{3}, 1.0\right) \times 15.0$
- **Historical Spend (10 pts)**: $\min\left(\frac{\text{total\_spend}}{4000}, 1.0\right) \times 10.0$

### Behavioral Archetype Calibration

| Archetype Profile | Engagement (30) | Cart (35) | Loyalty (35) | Expected Score | Classification |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **VIP Repeat Buyer** (₹3,500 cart, 18 min site, 3 prior orders) | 28.5 | 35.0 | 35.0 | **98.5** | Tier 1: Urgent Instant Recovery |
| **First-Time High Intent** (₹2,200 cart, 15 min site, 0 prior orders) | 25.0 | 32.3 | 2.0 | **59.3** | Tier 2: Discount/Incentive Nudge |
| **Quick Low-Value Cart** (₹300 cart, 3 min site, 1 prior order) | 5.5 | 26.0 | 7.0 | **38.5** | Tier 3: Standard Reminder |
| **Casual Window Shopper** (0 cart, 1.5 min site, 0 prior orders) | 2.5 | 0.0 | 2.0 | **4.5** | Tier 4: No Recovery Action |

---

## 7. Missing Value & Imputation Strategies

The pipeline adopts strict, domain-appropriate data imputation rules to prevent numerical skewing:

| Field Category | Column Example | Strategy Applied | Rationale |
| :--- | :--- | :--- | :--- |
| **Monetary & Quantities** | `unit_price`, `quantity`, `discount_amount` | Median imputation & lower bound clipping | Preserves standard pricing distributions; prevents negative values or zero division. |
| **Engagement Metrics** | `pages_viewed`, `time_on_site_sec` | Clip to non-negative ($pages \ge 1, duration \ge 0$) | Ensures valid denominator inputs for intent scoring. |
| **Binary Flags** | `added_to_cart`, `purchased`, `cart_abandoned` | Explicit Boolean coercion $\{0, 1\}$ | Guarantees exact conditional routing without null propagation. |
| **Categoricals** | `session_duration_bucket`, `device_type` | Label with `"unknown"` or preserve code | Prevents accidental synthetic category creation. |
| **Timestamps** | `visit_date` | Format parsing (`%d-%m-%Y`) with fallback epoch | Retains chronological ordering for customer aggregation. |
