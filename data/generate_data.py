"""
Generates a realistic synthetic dataset of job applications for a fresher
Data Science / Software Engineering job search.

This is SYNTHETIC data (randomly generated with realistic distributions),
not real personal application records — safe to publish on a public repo.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

COMPANIES = [
    ("Niveus Solutions", "Mangaluru", "Product/Services", "Mid-size"),
    ("Winman Software", "Mangaluru", "Product", "Mid-size"),
    ("Novigo Solutions", "Mangaluru", "Product", "Small"),
    ("Robosoft Technologies", "Mangaluru", "Product", "Mid-size"),
    ("Invenger Technologies", "Mangaluru", "Services", "Small"),
    ("Infosys", "Bangalore", "IT Services", "MNC"),
    ("Mphasis", "Bangalore", "IT Services", "MNC"),
    ("TCS", "Chennai", "IT Services", "MNC"),
    ("HARMAN", "Bangalore", "Product", "MNC"),
    ("Avishkar AI", "Mangaluru", "Startup", "Startup"),
    ("Raktrix Technologies", "Bangalore", "Startup", "Startup"),
    ("NextAstra Technologies", "Pune", "Product", "Startup"),
    ("MRPL", "Mangaluru", "Core/PSU", "Large"),
    ("MNJ Software", "Bangalore", "Services", "Small"),
    ("Microsoft", "Bangalore", "Product", "MNC"),
    ("Wipro", "Bangalore", "IT Services", "MNC"),
    ("Zoho", "Chennai", "Product", "MNC"),
    ("Freshworks", "Chennai", "Product", "MNC"),
    ("Capgemini", "Bangalore", "IT Services", "MNC"),
    ("Accenture", "Bangalore", "IT Consulting", "MNC"),
    ("Deloitte", "Bangalore", "IT Consulting", "MNC"),
    ("Cognizant", "Chennai", "IT Services", "MNC"),
    ("PwC", "Bangalore", "IT Consulting", "MNC"),
    ("Persistent Systems", "Pune", "Product", "Mid-size"),
    ("OmneNEST Technologies", "Mangaluru", "Services", "Small"),
    ("Microgreen Technologies", "Mangaluru", "Services", "Small"),
]

ROLE_TYPES = [
    ("Data Science", 0.28),
    ("Data Analytics", 0.20),
    ("Software Engineering", 0.27),
    ("AI/ML Engineering", 0.15),
    ("IT Consulting", 0.10),
]

SOURCES = ["LinkedIn", "Naukri", "Company Website", "Referral", "Campus/Off-campus Drive", "Instahyre"]

STAGES = [
    "Applied",
    "Rejected - No Response",
    "Rejected After Screening",
    "Online Assessment",
    "Technical Interview",
    "HR Interview",
    "Offer",
]

# Stage progression probabilities (roughly realistic for a fresher market)
STAGE_WEIGHTS = [0.30, 0.28, 0.14, 0.12, 0.09, 0.05, 0.02]

SKILL_GAPS_POOL = [
    "LangChain", "LlamaIndex", "RAG Pipelines", "Vector Databases",
    "Docker", "Power BI", "Tableau", "Kubernetes", "AWS", "Spark",
    "System Design", "SQL Advanced", None, None, None,  # some apps have no flagged gap
]

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def generate_applications(n=85):
    start_date = datetime(2026, 3, 1)
    end_date = datetime(2026, 8, 6)

    records = []
    for i in range(n):
        company, location, org_type, company_size = random.choice(COMPANIES)
        role_type = np.random.choice(
            [r[0] for r in ROLE_TYPES], p=[r[1] for r in ROLE_TYPES]
        )
        source = random.choice(SOURCES)
        applied_on = random_date(start_date, end_date)
        stage = np.random.choice(STAGES, p=STAGE_WEIGHTS)
        remote = random.choice([True, False, False])  # ~1/3 remote
        skill_gap = random.choice(SKILL_GAPS_POOL)

        days_to_response = None
        if stage != "Applied":
            days_to_response = int(np.random.gamma(3, 3))  # realistic right-skew

        records.append({
            "application_id": f"APP-{i+1:03d}",
            "company": company,
            "location": location,
            "remote_option": remote,
            "org_type": org_type,
            "company_size": company_size,
            "role_type": role_type,
            "source": source,
            "applied_on": applied_on.strftime("%Y-%m-%d"),
            "stage": stage,
            "days_to_response": days_to_response,
            "flagged_skill_gap": skill_gap,
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic job application dataset.")
    parser.add_argument("-n", "--num-records", type=int, default=85, help="Number of records to generate (default: 85)")
    parser.add_argument("-o", "--output", type=str, default="applications.csv", help="Output CSV filepath")
    args = parser.parse_args()

    df = generate_applications(args.num_records)
    df.to_csv(args.output, index=False)
    print(f"Generated {len(df)} synthetic application records -> {args.output}")
    print(df.head())