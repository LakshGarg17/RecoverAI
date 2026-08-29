import os
import sys
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

# Ensure standard output can print Unicode characters on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure database and backend packages can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_path = os.path.join(root_dir, "backend")
for path in [root_dir, backend_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from database.database import SessionLocal, init_db, engine, Base
from database.models import Customer, Transaction, RecoveryCase

# Set random seed for reproducibility
random.seed(42)

# Names pool for realistic Indian & Global customer generation
FIRST_NAMES = [
    "Aarav", "Aditi", "Ananya", "Amit", "Arjun", "Deepak", "Divya", "Gaurav",
    "Ishaan", "Kavya", "Manish", "Neha", "Nikhil", "Pooja", "Pranav", "Priya",
    "Rahul", "Rhea", "Rohan", "Sanjay", "Shreya", "Sneha", "Tanvi", "Varun",
    "Vikram", "Abhishek", "Alok", "Bhavna", "Chirag", "Farhan", "Harish",
    "Karan", "Meera", "Nandini", "Pallavi", "Rajesh", "Sakshi", "Tarun", "Yash",
    "Alex", "David", "Emily", "James", "Sarah", "Michael", "Elena", "Marcus"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Mehta", "Gupta", "Iyer", "Nair", "Reddy",
    "Singh", "Kumar", "Kapoor", "Chopra", "Joshi", "Bhatia", "Deshmukh",
    "Chatterjee", "Banerjee", "Menon", "Pillai", "Agarwal", "Saxena", "Malhotra",
    "Kulkarni", "Chauhan", "Rao", "Shetty", "Das", "Roy", "Sen", "Mishra",
    "Smith", "Johnson", "Williams", "Brown", "Taylor", "Davies", "Wilson"
]

EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "icloud.com", "proton.me",
    "techcorp.in", "finserve.co", "growthstack.io", "retailhub.com", "nexusecom.in"
]

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET"]
PAYMENT_METHOD_WEIGHTS = [0.48, 0.32, 0.12, 0.08]

FAILURE_REASONS_BY_METHOD = {
    "UPI": {
        "bank_timeout": 0.38,
        "bank_decline": 0.25,
        "network_error": 0.22,
        "insufficient_funds": 0.10,
        "unknown": 0.05,
    },
    "CARD": {
        "insufficient_funds": 0.30,
        "authentication_failed": 0.28,
        "payment_method_expired": 0.20,
        "bank_decline": 0.17,
        "unknown": 0.05,
    },
    "NETBANKING": {
        "bank_timeout": 0.40,
        "bank_decline": 0.25,
        "network_error": 0.20,
        "authentication_failed": 0.10,
        "unknown": 0.05,
    },
    "WALLET": {
        "insufficient_funds": 0.45,
        "bank_decline": 0.25,
        "network_error": 0.15,
        "bank_timeout": 0.10,
        "unknown": 0.05,
    },
}


def weighted_choice(choices_dict: Dict[str, float]) -> str:
    """Select a key from a dictionary of choices and their float weights."""
    items = list(choices_dict.keys())
    weights = list(choices_dict.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_customer_profile(index: int, archetype: str) -> Tuple[Customer, List[Dict[str, Any]]]:
    """
    Generate a customer and their full transaction history based on archetype.
    """
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    domain = random.choice(EMAIL_DOMAINS)
    # Ensure unique email
    clean_name = f"{first_name.lower()}.{last_name.lower()}{index}"
    email = f"{clean_name}@{domain}"
    customer_id = f"cust_{uuid.uuid4().hex[:12]}"

    now = datetime.utcnow()

    # Configure Archetype parameters
    if archetype == "Loyal":
        # ~12 txns (range 11-13), ~11 successful, high lifetime value over 60-90 days
        txn_count = random.randint(11, 13)
        customer_days_ago = random.randint(60, 90)
        # ~92% success rate
        status_pool = ["success"] * 12 + ["failed"] * 1
        amount_range = (800.0, 4500.0)

    elif archetype == "New":
        # 1 transaction, failed/abandoned, recently joined (1-20 days ago)
        txn_count = 1
        customer_days_ago = random.randint(1, 20)
        status_pool = ["failed", "failed", "abandoned", "pending"]
        amount_range = (500.0, 3500.0)

    elif archetype == "High-value":
        # ~5 txns (range 4-6), INR 50,000+ total volume, mostly successful (~80%)
        txn_count = random.randint(4, 6)
        customer_days_ago = random.randint(45, 80)
        status_pool = ["success", "success", "success", "success", "failed", "pending"]
        amount_range = (12000.0, 35000.0)

    elif archetype == "Problematic":
        # ~7 txns (range 6-8), roughly 40% success rate, frequent declines/timeouts
        txn_count = random.randint(6, 8)
        customer_days_ago = random.randint(40, 75)
        status_pool = ["failed", "failed", "failed", "abandoned", "abandoned", "success", "success", "pending"]
        amount_range = (600.0, 6000.0)

    else:  # "Standard"
        # ~4 txns (range 3-5), ~75-80% success rate, regular everyday mix
        txn_count = random.randint(3, 5)
        customer_days_ago = random.randint(30, 60)
        status_pool = ["success", "success", "success", "success", "failed", "abandoned", "pending"]
        amount_range = (400.0, 5000.0)

    customer_created_at = now - timedelta(days=customer_days_ago, minutes=random.randint(0, 1440))

    # Generate chronologically distributed transactions for this customer
    transactions_data = []
    time_span_days = max(1, customer_days_ago)
    day_step = time_span_days / max(1, txn_count)

    successful_count = 0
    failed_count = 0
    lifetime_val = 0.0

    for t_idx in range(txn_count):
        # Calculate timestamp with positive progression
        offset_days = min(time_span_days, (t_idx * day_step) + random.uniform(0.1, max(0.2, day_step * 0.9)))
        txn_time = customer_created_at + timedelta(days=offset_days, minutes=random.randint(5, 300))
        if txn_time > now:
            txn_time = now - timedelta(minutes=random.randint(5, 60))

        status = random.choice(status_pool)
        amount = round(random.uniform(*amount_range), 2)
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS, k=1)[0]

        # Determine failure reason
        failure_reason = None
        if status in ["failed", "abandoned"]:
            failure_reason = weighted_choice(FAILURE_REASONS_BY_METHOD[payment_method])

        if status == "success":
            successful_count += 1
            lifetime_val += amount
        elif status == "failed":
            failed_count += 1

        txn_id = f"txn_{uuid.uuid4().hex[:14]}"

        transactions_data.append({
            "transaction_id": txn_id,
            "customer_id": customer_id,
            "amount": amount,
            "currency": "INR",
            "payment_method": payment_method,
            "status": status,
            "failure_reason": failure_reason,
            "created_at": txn_time,
        })

    # Sort transactions chronologically
    transactions_data.sort(key=lambda x: x["created_at"])

    customer = Customer(
        customer_id=customer_id,
        name=name,
        email=email,
        total_transactions=len(transactions_data),
        successful_transactions=successful_count,
        failed_transactions=failed_count,
        lifetime_value=round(lifetime_val, 2),
        created_at=customer_created_at,
    )

    return customer, transactions_data


def generate_seed_data(
    num_loyal: int = 200,
    num_new: int = 250,
    num_high_val: int = 100,
    num_problematic: int = 150,
    num_standard: int = 300,
    recovery_case_sample_rate: float = 0.35,
) -> Tuple[List[Customer], List[Transaction], List[RecoveryCase]]:
    """
    Generate ~1,000 customers, ~5,000 transactions, and candidate RecoveryCases.
    """
    customers: List[Customer] = []
    transactions: List[Transaction] = []
    recovery_cases: List[RecoveryCase] = []

    archetype_plan = [
        ("Loyal", num_loyal),
        ("New", num_new),
        ("High-value", num_high_val),
        ("Problematic", num_problematic),
        ("Standard", num_standard),
    ]

    total_target_customers = sum(count for _, count in archetype_plan)
    cust_counter = 0

    print(f"[*] Generating {total_target_customers:,} realistic customers across 5 archetypes...")

    for archetype, count in archetype_plan:
        for _ in range(count):
            cust_counter += 1
            customer_obj, txns_raw = generate_customer_profile(cust_counter, archetype)
            customers.append(customer_obj)

            for t_raw in txns_raw:
                txn_obj = Transaction(**t_raw)
                transactions.append(txn_obj)

                # Identify potential recovery cases:
                # Failed or abandoned transactions qualify as recovery candidates
                if txn_obj.status in ["failed", "abandoned"]:
                    # Create recovery cases for a realistic proportion of failures
                    if random.random() < recovery_case_sample_rate:
                        case_id = f"case_{uuid.uuid4().hex[:12]}"
                        recovery_case = RecoveryCase(
                            case_id=case_id,
                            transaction_id=txn_obj.transaction_id,
                            amount_at_risk=txn_obj.amount,
                            risk_score=None,                # To be populated in Day 3
                            recovery_probability=None,      # To be populated in Day 3/4
                            recommended_action=None,        # To be populated in Day 3/4
                            status="pending",
                            attempt_count=0,
                            amount_recovered=0.0,
                            created_at=txn_obj.created_at,
                            updated_at=txn_obj.created_at,
                        )
                        recovery_cases.append(recovery_case)

    return customers, transactions, recovery_cases


def seed_database():
    """
    Main seeding routine: Cleans schema and batch inserts synthetic data.
    """
    print("\n=======================================================")
    print("  RecoverAI - Synthetic Data Generator & Seeder (Day 2)")
    print("=======================================================\n")

    print("[1/4] Re-initializing database schema...")
    init_db(drop_all=True)

    session = SessionLocal()
    try:
        print("[2/4] Generating synthetic profiles & transaction histories...")
        customers, transactions, recovery_cases = generate_seed_data(
            num_loyal=200,
            num_new=250,
            num_high_val=100,
            num_problematic=150,
            num_standard=300,
            recovery_case_sample_rate=0.35,
        )

        print(f"[3/4] Writing records to database...")
        print(f"      - Adding {len(customers):,} Customers...")
        session.bulk_save_objects(customers)
        session.commit()

        print(f"      - Adding {len(transactions):,} Transactions...")
        session.bulk_save_objects(transactions)
        session.commit()

        print(f"      - Adding {len(recovery_cases):,} Recovery Cases...")
        session.bulk_save_objects(recovery_cases)
        session.commit()

        print("[4/4] Computing analytics summary...")

        # Compute summary metrics for console report
        total_volume = sum(t.amount for t in transactions)
        successful_volume = sum(t.amount for t in transactions if t.status == "success")
        at_risk_volume = sum(rc.amount_at_risk for rc in recovery_cases)

        status_counts = {}
        for t in transactions:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1

        method_counts = {}
        for t in transactions:
            method_counts[t.payment_method] = method_counts.get(t.payment_method, 0) + 1

        reason_counts = {}
        for t in transactions:
            if t.failure_reason:
                reason_counts[t.failure_reason] = reason_counts.get(t.failure_reason, 0) + 1

        print("\n" + "=" * 60)
        print("                 SEEDING SUMMARY REPORT")
        print("=" * 60)
        print(f"Total Customers Created    : {len(customers):>8,}")
        print(f"Total Transactions Created : {len(transactions):>8,}")
        print(f"Total Recovery Cases Ready : {len(recovery_cases):>8,}")
        print(f"Total Processed Volume     : INR {total_volume:>12,.2f}")
        print(f"Successful Volume (LTV)    : INR {successful_volume:>12,.2f}")
        print(f"Recovery Amount at Risk    : INR {at_risk_volume:>12,.2f}")
        print("-" * 60)
        print("TRANSACTIONS BY STATUS:")
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            pct = (count / len(transactions)) * 100
            print(f"  * {status.capitalize():<16} : {count:>6,} ({pct:>5.1f}%)")
        print("-" * 60)
        print("TRANSACTIONS BY PAYMENT METHOD:")
        for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
            pct = (count / len(transactions)) * 100
            print(f"  * {method:<16} : {count:>6,} ({pct:>5.1f}%)")
        print("-" * 60)
        print("FAILURE REASONS DISTRIBUTION:")
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
            pct = (count / sum(reason_counts.values())) * 100
            print(f"  * {reason:<24} : {count:>6,} ({pct:>5.1f}%)")
        print("=" * 60)
        print("\n[+] Database seeding completed successfully! Ready for Day 3 Risk Engine.\n")

    except Exception as e:
        session.rollback()
        print(f"\n[!] Error seeding database: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
