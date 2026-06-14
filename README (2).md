# Potomac Federal Office Building — Project Controls Dashboard

**A full-lifecycle project controls solution simulating a $45M GSA federal office building construction project. Built to demonstrate earned value management, CPM scheduling, risk analysis, and change order tracking — the core competencies of a Project Controls Analyst in the AEC industry.**

---

## Project Overview

| Field | Detail |
|---|---|
| **Project** | Potomac Federal Office Building — New Construction |
| **Client** | U.S. General Services Administration (GSA) |
| **Contract Type** | Lump Sum — Design-Bid-Build |
| **Original Contract Value** | $45,000,000 |
| **Approved Changes** | $1,658,000 |
| **Revised Contract Value** | $46,658,000 |
| **Project Duration** | 24 Months (Jan 2023 — Dec 2024) |
| **Reporting Through** | June 2024 (Month 18) |
| **Role Simulated** | Project Controls Analyst — Owner's Representative |
| **Location** | Washington, DC Metro Area |

---

## Dashboard Pages

### 1. Executive Summary
High-level KPI overview for project leadership and client reporting. Displays BAC, ACWP, BCWP, EAC, CPI, SPI, and VAC with conditional formatting — red for underperformance, green for on-target. Includes project information card and budget utilization donut chart.

### 2. EVM Performance
Detailed earned value analysis by work package. Features:
- CPI vs SPI clustered bar chart with 1.0 target line
- EVM metrics table with conditional formatting on all variance columns
- Cost variance waterfall chart identifying overrun drivers by work package
- CPI vs TCPI gauge visual — the reality check on budget recoverability

### 3. S-Curve
Cumulative cost and schedule performance plotted over 24 months. Three lines tell the project story:
- **BCWS** (gray dashed) — the baseline plan
- **BCWP** (blue solid) — earned value actually achieved
- **ACWP** (red solid) — actual money spent

The widening gap between lines from Month 4 onwards traces directly to the geotechnical surprise on foundations.

### 4. Schedule & Critical Path
CPM activity register with 31 activities across 8 work packages. Features:
- Full activity table with planned start/finish, duration, float, and predecessor logic
- Critical path highlighting — 20 of 31 activities with zero float
- Float distribution bar chart identifying near-critical activities
- Activity duration by work package — critical vs non-critical split

### 5. Risk Register
10-item risk register with probability/impact scoring, cost and schedule exposure quantification, and mitigation tracking. Features:
- Full risk register table with conditional formatting by status and impact
- Risk matrix (3×3 probability vs impact heat map)
- Cost exposure by risk category bar chart
- Summary cards: total exposure, open risks, schedule exposure days

### 6. Change Order Log
Complete change order tracking from submission through approval. Features:
- Full CO table with status, cost impact, schedule impact, and cause
- Cost impact by category (approved vs pending split)
- Change order timeline showing cadence of changes through project lifecycle
- Summary cards: total CO value, approved, pending, schedule impact

---

## Project Status at Month 18 — Key Findings

| Metric | Value | Interpretation |
|---|---|---|
| **CPI** | 0.95 | Spending $1.05 for every $1.00 of work delivered |
| **SPI** | 0.82 | Only 82% of planned work completed on schedule |
| **EAC** | $47.42M | Forecast overrun of $2.42M against $45M BAC |
| **VAC** | -$2.42M | Project tracking over budget at completion |
| **TCPI** | 1.12 | Would need 12% efficiency gain to recover budget — unrealistic |
| **Open Risks** | 8 | $1.71M total cost exposure remaining |
| **Approved COs** | 8 | $1.38M in approved changes (3.07% of contract) |
| **Pending COs** | 2 | $275K awaiting owner approval |

---

## Root Cause Narrative

The project performance issues trace to a single originating event — **undisclosed underground obstructions discovered during geotechnical investigation in Month 2** (R001, CO-001). This triggered:

1. **$412K additional piling work** — consuming foundation float and pushing the critical path
2. **Cascade delay to structural concrete frame** — 8 weeks behind planned start
3. **Curtain wall procurement overlap** — delivery window compressed, leading to CO-005
4. **MEP coordination rework** — reduced installation window forced sequencing conflicts

By Month 18, the cumulative effect is a **-$6.6M schedule variance** and **-$1.6M cost variance**. The TCPI of 1.12 signals that full budget recovery is not achievable without a scope or budget adjustment — the honest conversation an owner's representative must have with the client.

---

## Technical Architecture

### Data Generation
- **Language:** Python 3
- **Libraries:** pandas, numpy
- **Approach:** Simulated project data generated via S-curve weighted distribution across 8 work packages and 24 reporting periods
- **Output:** 6 CSV files forming a star schema

### Data Model (Star Schema)

```
                    ┌─────────────┐
                    │  Dim_Date   │
                    │  (24 rows)  │
                    └──────┬──────┘
                           │
          ┌────────────────▼────────────────┐
          │           evm_monthly           │
          │     (192 rows — fact table)     │
          └────────────────┬────────────────┘
                           │
          ┌────────────────▼────────────────┐
          │              wbs                │
          │      (9 rows — dim table)       │
          └──┬──────────┬──────────┬────────┘
             │          │          │
    ┌─────────▼──┐ ┌────▼──────┐ ┌▼──────────────┐ ┌──────────────────┐
    │  schedule  │ │  risk_    │ │ change_orders  │ │  project_info    │
    │ (31 rows)  │ │ register  │ │   (10 rows)    │ │  (reference)     │
    └────────────┘ │ (10 rows) │ └────────────────┘ └──────────────────┘
                   └───────────┘
```

### DAX Measures (12 core EVM measures)

| Measure | Formula | Purpose |
|---|---|---|
| BCWS | SUM of planned period spend | Baseline plan |
| BCWP | SUM of earned period value | True progress |
| ACWP | SUM of actual period spend | Real cost |
| BAC | MAX BAC per WBS (ALL dates) | Fixed contract value |
| CPI | BCWP / ACWP | Cost efficiency |
| SPI | BCWP / BCWS | Schedule efficiency |
| CV | BCWP - ACWP | Cost variance (dollars) |
| SV | BCWP - BCWS | Schedule variance (dollars) |
| EAC | BAC / CPI | Forecast final cost |
| ETC | EAC - ACWP | Remaining budget needed |
| VAC | BAC - EAC | Forecast overrun/saving |
| TCPI | (BAC-BCWP) / (BAC-ACWP) | Required future efficiency |

---

## Files in this Repository

```
├── README.md
├── data/
│   ├── generate_data.py        # Python script — generates all CSV files
│   ├── wbs.csv                 # Work breakdown structure (9 rows)
│   ├── evm_monthly.csv         # EVM performance by package by period (192 rows)
│   ├── schedule.csv            # CPM activity schedule (31 activities)
│   ├── risk_register.csv       # Risk register (10 risks)
│   ├── change_orders.csv       # Change order log (10 COs)
│   └── project_info.csv        # Project reference information
└── dashboard/
    └── PFOB_ProjectControls.pbix   # Power BI Desktop file
```

---

## How to Run

### Generate the Data
```bash
# Clone the repository
git clone https://github.com/brkshnf-cmyk/federal-office-project-controls

# Install dependencies
pip install pandas numpy

# Generate all CSV files
python data/generate_data.py
```

### Open the Dashboard
1. Download and install [Power BI Desktop](https://powerbi.microsoft.com/desktop) (free)
2. Open `dashboard/PFOB_ProjectControls.pbix`
3. If prompted to refresh data, point the data source to the `/data` folder
4. Use the Period slicer to navigate through the 24-month project timeline

---

## Domain Background

This project was designed by a civil/structural engineer with six years of field experience on large infrastructure projects — including construction inspection, concrete testing, quantity measurement, and multi-discipline coordination. The scenario, cost drivers, risk events, and change order causes are grounded in real construction project dynamics:

- Geotechnical surprises are the most common source of foundation cost overruns on urban building projects
- Curtain wall procurement is typically on the critical path for high-rise construction and carries long lead times
- MEP coordination conflicts are the leading cause of rework in building construction
- A 3–5% change order rate is typical for federal lump-sum contracts

The EVM methodology follows **ANSI/EIA-748** standards as applied in federal project controls environments.

---

## Skills Demonstrated

- **Earned Value Management** — CPI, SPI, EAC, VAC, TCPI, CV, SV
- **CPM Scheduling** — Activity sequencing, predecessor logic, float analysis, critical path identification
- **Risk Management** — Risk register development, probability/impact scoring, cost and schedule exposure quantification
- **Change Control** — Change order tracking, cause analysis, approval workflow
- **Power BI** — Star schema data modeling, advanced DAX measures, conditional formatting, multi-page dashboard design
- **Python** — Synthetic data generation, S-curve distribution modeling, pandas data engineering
- **AEC Domain Knowledge** — Construction project lifecycle, structural building systems, owner's representative controls function

---

## Author

**Brook Weldegebriel**
Civil Engineer | Project Controls Analyst | Data Analyst

- GitHub: [github.com/brkshnf-cmyk](https://github.com/brkshnf-cmyk)
- Email: brookms2023@gmail.com
- Location: Clarksburg, MD

*Six years of construction field experience + three years of analytics practice — project controls outputs that are operationally grounded, not just technically produced.*
