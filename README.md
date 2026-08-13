# 📊 Job Search Analytics Dashboard

![CI Pipeline](https://github.com/Vivekjpoojary/job-search-analytics/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.20%2B-3F4F75?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green)

An interactive, Power BI/Tableau-style analytics dashboard — built entirely in
Python — that tracks and visualizes a fresher tech job search: application
funnel conversion, response times, most-flagged skill gaps, and role/location
trends.

**Why this project?** As a fresher applying for Data Science / Analytics /
Software Engineering roles, I wanted to *apply* data analytics rather than
just list it as a skill — so I built a tool to track my own application
pipeline the way a recruiter or BI analyst would track a sales funnel.

🔗 **Portfolio:** [vivekjpoojary.vercel.app](https://vivekjpoojary.vercel.app)

---

## Features

- **KPI Summary & Velocity Metrics** — total applications, response rate, interview conversion, offers, avg/median response times, 7d/30d submission velocity, WoW growth, and peak submission day
- **Automated Insights Engine** — dynamic, data-driven recommendations highlighting highest-converting org types, top channel performance, application velocity trends, and key skill bottlenecks
- **Application Funnel & Conversion Rates** — step-by-step conversion analytics between consecutive stages (Applied → Online Assessment → Technical → HR → Offer)
- **Application Channel Performance** — breakdown of response rate % and interview rate % across platforms (LinkedIn, Naukri, Referrals, Instahyre, etc.)
- **Pending SLA Tracker** — automated warning system detecting applications stuck in "Applied" state over 21 days
- **Estimated Compensation (CTC) Analysis** — distribution of CTC ranges across role types
- **Outcome Breakdown** — donut chart of application outcomes
- **Timeline** — weekly application volume
- **Role Type Distribution** — Data Science / Analytics / SWE / AI-ML / IT Consulting
- **Skill-Gap Frequency** — most commonly flagged missing skills across rejections
- **Response Rate by Company Type** — MNC vs Startup vs Mid-size vs Services
- **Multi-Parameter Filters** — company/skill keyword search, role type, location, remote toggle, and date range filter
- **Raw Data Explorer & CSV Export** — sortable/filterable table with 1-click CSV download
- **Automated CI/CD** — GitHub Actions test matrix across Python 3.10, 3.11, 3.12, and 3.13

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| Dashboard framework | Streamlit |
| Visualization | Plotly Express & Graph Objects |
| Data handling | Pandas / NumPy |
| Testing & Quality | Python Unittest, Pytest, Coverage, Ruff |
| CI/CD Pipeline | GitHub Actions Workflow |

## Project Structure

```
job-search-analytics/
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI matrix pipeline (Python 3.10-3.13)
├── app.py                  # Streamlit dashboard app, analytics logic & UI layout
├── data/
│   ├── generate_data.py    # Synthetic dataset generator with seed support & CTC modeling
│   └── applications.csv    # Generated application dataset
├── tests/
│   └── test_data.py        # Comprehensive unit test suite (13 tests)
├── .streamlit/
│   └── config.toml         # Custom Streamlit theme config
├── pyproject.toml          # Tooling configuration (pytest, coverage, ruff)
├── requirements.txt        # Application dependencies
└── README.md               # Project documentation
```

## Running Locally

```bash
git clone https://github.com/Vivekjpoojary/job-search-analytics.git
cd job-search-analytics
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Running Tests

Execute the automated test suite locally:

```bash
PYTHONPATH=. python -m unittest discover tests
```

## Regenerating the Dataset

The included `data/applications.csv` is **synthetic data** (randomly
generated with realistic distributions) — not real personal application
records, since actual application details aren't meant for a public repo.
To regenerate it with different parameters or a fixed seed:

```bash
cd data
python generate_data.py -n 85 --seed 42 -o applications.csv
```

## Deployment

This app deploys for free on [Streamlit Community Cloud](https://streamlit.io/cloud):
1. Push this repo to GitHub
2. Go to share.streamlit.io → New app → select this repo → `app.py`
3. Deploy, then paste the live link back into this README

## Roadmap / Ideas for Extension

- [ ] Connect to a live Google Sheets tracker instead of static CSV
- [ ] Add a "predicted response likelihood" model (ties into ML skills)
- [ ] Export filtered view as PDF report
- [ ] Add SQL backend (SQLite) instead of CSV for a data-engineering angle

## Author

**Vivek J Poojary**
BCA Graduate, St. Aloysius (Deemed to be University), Mangaluru
[GitHub](https://github.com/Vivekjpoojary) · [LinkedIn](https://linkedin.com/in/vivekjpoojary) · [Portfolio](https://vivekjpoojary.vercel.app)
