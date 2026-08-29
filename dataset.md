# RecoverAI Dataset Documentation

## 1. Overview & Source

RecoverAI utilizes real e-commerce transactional and browsing session data sourced from Kaggle to simulate and power its autonomous payment recovery intelligence layer.

- **Data Source**: Indian E-Commerce Customer Behavior & Transaction Dataset
- **Origin / Reference**: [Kaggle E-Commerce Dataset](https://www.kaggle.com/datasets)
- **Format**: CSV (`indian_ecommerce.csv`)
- **Scale**: 25,000 recorded user sessions across 8,442 unique Indian retail customers (spanning January 2024 to October 2024).
- **License / Usage**: Open educational and benchmarking license for ML development and decision intelligence modeling.

---

## 2. Core Repository Principle: Raw Immutability

> [!IMPORTANT]
> **Strict Raw Data Principle**: The original Kaggle file in `data/raw/indian_ecommerce.csv` is **read-only and immutable**. It is never modified or overwritten by any script. All cleaning, normalization, intent scoring, and canonical mapping occur strictly in memory and output into `data/processed/recoverai_events.csv`.

### Directory Layout & Git Policy
```
data/
├── raw/
│   └── indian_ecommerce.csv       <- Untouched raw Kaggle source (untracked in git)
├── processed/
│   └── recoverai_events.csv       <- Canonical RecoverAI recovery events (untracked in git)
└── samples/
    └── recoverai_sample.csv       <- 100-row representative sample (tracked in git)
```

Both `data/raw/` and `data/processed/` are excluded via `.gitignore` to prevent large binary blobs in source control, while `data/samples/recoverai_sample.csv` is tracked so developers and hackathon judges can immediately inspect the data shape.

---

## 3. Raw Kaggle Dataset Schema

| Column | Raw Type | Description |
| :--- | :--- | :--- |
| `customer_id` | `int64` | Identifier for the unique customer |
| `session_id` | `int64` | Unique web browsing / shopping session identifier |
| `visit_date` | `object` | Session date (DD-MM-YYYY) |
| `device_type` | `int64` | Coded device type (0: Desktop, 1: Mobile, 2: Tablet) |
| `user_type` | `int64` | 0: Returning, 1: New |
| `marketing_channel` | `int64` | Traffic source channel (0 to 5) |
| `product_id` | `int64` | Catalog item ID |
| `product_category` | `int64` | Item category code (0 to 7) |
| `unit_price` | `float64` | Item price in Indian Rupees (INR) |
| `quantity` | `int64` | Selected item quantity |
| `discount_percent` | `int64` | Applied promotional discount percentage |
| `discount_amount` | `float64` | Absolute discount in INR |
| `revenue` | `float64` | Final transaction amount (positive if purchased, 0.0 if not completed) |
| `pages_viewed` | `int64` | Total pages browsed during the session |
| `time_on_site_sec` | `int64` | Total session engagement duration in seconds |
| `added_to_cart` | `int64` | Flag indicating whether items were added to cart (1 = Yes, 0 = No) |
| `purchased` | `int64` | Purchase completion status (1 = Completed, 0 = Not completed) |
| `cart_abandoned` | `int64` | Cart abandonment flag (1 = Abandoned, 0 = Not abandoned) |
| `rating` | `int64` | Post-purchase or session feedback score (1 to 5) |
| `review_text` | `int64` | Encoded review sentiment |
| `review_helpful_votes` | `int64` | Helpful votes for user reviews |
| `payment_method` | `int64` | Payment instrument code (0: UPI, 1: CARD, 2: DEBIT_CARD, 3: NETBANKING, 4: WALLET, 5: COD_EMI) |
| `visit_day`, `visit_month`, `visit_weekday`, `visit_season` | `int64` | Temporal attributes |
| `session_duration_bucket` | `object` | Binned session duration category |
| `revenue_normalized` | `float64` | Normalized scale metric |
| `location` | `int64` | Regional demographic code |

---

## 4. RecoverAI Canonical Recovery Events Schema

To provide a consistent API and database abstraction across diverse payment gateways (Razorpay, Stripe, Cashfree) and e-commerce platforms (Shopify, WooCommerce, custom checkout), the pipeline transforms the raw records into the **RecoverAI Canonical Schema**:

| Field | Data Type | Description |
| :--- | :--- | :--- |
| `event_id` | `String` | Formatted event identifier (`evt_000001`) |
| `customer_id` | `String` | Canonical customer identifier (`cust_01803`) |
| `session_id` | `String` | Canonical session identifier (`sess_000001`) |
| `amount` | `Float` | Event monetary value (completed purchase amount or cart value) in INR |
| `currency` | `String` | ISO currency code (`INR`) |
| `payment_method` | `String` | Standardized payment instrument (`UPI`, `CARD`, `DEBIT_CARD`, `NETBANKING`, `WALLET`, `COD_EMI`) |
| `event_type` | `String` | Event category (`cart_abandoned`, `purchase_completed`, `page_browse`) |
| `purchase_status` | `String` | High-level status (`abandoned`, `completed`, `browsing`) |
| `cart_value` | `Float` | Net monetary value of items placed in cart `(unit_price * quantity) - discount` |
| `session_duration` | `Integer` | Time spent on site in seconds |
| `pages_viewed` | `Integer` | Page count explored during session |
| `purchase_history` | `Integer` | Total prior successful transactions completed by this customer |
| `customer_lifetime_value` | `Float` | Total historical spend by this customer |
| `purchase_intent_score` | `Float` | Behavioral intent score (0.00 – 100.00) |
| `revenue_at_risk` | `Float` | Potential revenue at risk in INR |
| `risk_score` | `Float (Nullable)` | *Reserved for Day 3 Risk Engine* |
| `recovery_probability` | `Float (Nullable)` | *Reserved for Day 3 ML Scoring* |
| `recommended_action` | `String (Nullable)` | *Reserved for Day 4 Autonomous Recovery Action Engine* |

---

## 5. Execution

To run the full inspection, cleaning, normalization, intent scoring, and canonical output generation:
```bash
python backend/data_pipeline/run_pipeline.py
```
