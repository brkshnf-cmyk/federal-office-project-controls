import pandas as pd
import numpy as np
from datetime import date, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

OUTPUT = "/home/claude/federal_office_controls"

# ── PROJECT PARAMETERS ──────────────────────────────────────────────────────
PROJECT_NAME   = "Potomac Federal Office Building – New Construction"
PROJECT_ID     = "PFOB-2023-001"
CONTRACT_VALUE = 45_000_000
START_DATE     = date(2023, 1, 2)
END_DATE       = date(2024, 12, 27)          # 24 months
TOTAL_MONTHS   = 24

# Reporting periods: end of each calendar month
def month_end_dates(start, n):
    dates = []
    d = start.replace(day=1)
    for _ in range(n):
        # move to first of next month then back one day
        if d.month == 12:
            nxt = d.replace(year=d.year+1, month=1, day=1)
        else:
            nxt = d.replace(month=d.month+1, day=1)
        dates.append(nxt - timedelta(days=1))
        d = nxt
    return dates

PERIODS = month_end_dates(START_DATE, TOTAL_MONTHS)

# ── WBS TABLE ────────────────────────────────────────────────────────────────
wbs_data = [
    # id, parent, name,                               level, bac,       csi_code,  planned_start,  planned_finish
    ("1",    None, "Potomac Federal Office Building",     1, 45_000_000, "",        "2023-01-02",  "2024-12-27"),
    ("1.1",  "1",  "Mobilization & Site Preparation",    2,  1_800_000, "01 50 00","2023-01-02",  "2023-03-31"),
    ("1.2",  "1",  "Deep Foundations & Basement",        2,  5_400_000, "03 10 00","2023-02-01",  "2023-06-30"),
    ("1.3",  "1",  "Structural Concrete Frame",          2,  9_000_000, "03 30 00","2023-05-01",  "2023-11-30"),
    ("1.4",  "1",  "Structural Steel & Metal Deck",      2,  7_200_000, "05 10 00","2023-09-01",  "2024-02-29"),
    ("1.5",  "1",  "Building Envelope",                  2,  6_300_000, "07 40 00","2023-11-01",  "2024-05-31"),
    ("1.6",  "1",  "MEP Rough-In",                       2,  7_650_000, "23 00 00","2024-01-01",  "2024-08-31"),
    ("1.7",  "1",  "Interior Finishes & Fit-Out",        2,  5_850_000, "09 00 00","2024-06-01",  "2024-11-30"),
    ("1.8",  "1",  "Commissioning & Closeout",           2,  1_800_000, "01 70 00","2024-10-01",  "2024-12-27"),
]

wbs_df = pd.DataFrame(wbs_data,
    columns=["WBS_ID","Parent_WBS","Work_Package","WBS_Level","BAC",
             "CSI_Code","Planned_Start","Planned_Finish"])
wbs_df.to_csv(f"{OUTPUT}/wbs.csv", index=False)
print("✓ wbs.csv")

# ── HELPER: date string → period index (0-based) ─────────────────────────────
def period_of(d_str):
    d = date.fromisoformat(d_str)
    for i, pe in enumerate(PERIODS):
        ps = (pe.replace(day=1))
        if ps <= d <= pe:
            return i
    if d < PERIODS[0]:
        return 0
    return TOTAL_MONTHS - 1

# ── SCHEDULE TABLE (CPM) ─────────────────────────────────────────────────────
# Each work package has activities; some are on critical path
schedule_rows = []
act_id = 1

# (wbs_id, activity, duration_days, lag_after_predecessor_days, predecessor_act_id, is_critical)
activities_template = [
    # 1.1 Mobilization
    ("1.1", "Site Clearing & Demolition",            30,  0,  None, True),
    ("1.1", "Temporary Facilities Setup",            20,  0,  1,    False),
    ("1.1", "Erosion & Sediment Control",            15,  5,  1,    False),
    # 1.2 Foundations
    ("1.2", "Geotechnical Investigation & Piling",   60,  0,  1,    True),
    ("1.2", "Pile Cap Concrete",                     45,  5,  4,    True),
    ("1.2", "Basement Retaining Walls",              40, 10,  5,    True),
    ("1.2", "Basement Slab-on-Grade",                20,  5,  6,    True),
    # 1.3 Concrete Frame
    ("1.3", "Column & Core Wall Formwork – L1-L4",  60,  0,  7,    True),
    ("1.3", "Rebar Installation – L1-L4",            45,  5,  8,    True),
    ("1.3", "Concrete Pour – L1-L4",                30,  5,  9,    True),
    ("1.3", "Column & Core Wall – L5-L8",           60,  0,  10,   True),
    ("1.3", "Concrete Pour – L5-L8",                30,  5,  11,   True),
    # 1.4 Steel
    ("1.4", "Structural Steel Erection – L1-L4",    45,  0,  10,   True),
    ("1.4", "Metal Deck Installation – L1-L4",      30,  5,  13,   True),
    ("1.4", "Structural Steel Erection – L5-Roof",  45, 10,  14,   True),
    ("1.4", "Metal Deck & Roof Framing",            30,  5,  15,   False),
    # 1.5 Envelope
    ("1.5", "Curtain Wall Fabrication & Delivery",  60,  0,  13,   False),
    ("1.5", "Curtain Wall Installation",            90,  5,  17,   True),
    ("1.5", "Roofing System",                       30, 10,  16,   False),
    # 1.6 MEP
    ("1.6", "MEP Coordination & BIM Clash Review",  30,  0,  14,   False),
    ("1.6", "Mechanical Ductwork Rough-In",         90,  5,  20,   True),
    ("1.6", "Electrical Conduit & Panel Rough-In",  75,  5,  20,   False),
    ("1.6", "Plumbing Rough-In",                    60,  5,  20,   False),
    ("1.6", "Fire Protection Rough-In",             45, 10,  20,   False),
    # 1.7 Finishes  (A26-A29)
    ("1.7", "Drywall & Partitions",                 60,  0,  21,   True),
    ("1.7", "Flooring & Ceiling Systems",           50,  5,  25,   True),
    ("1.7", "Painting & Wall Finishes",             35,  5,  26,   False),
    ("1.7", "Doors, Frames & Hardware",             25, 10,  26,   False),
    # 1.8 Closeout (A30-A32)
    ("1.8", "Systems Testing & Balancing",          30,  0,  26,   True),
    ("1.8", "Pre-Final Inspection & Punch List",    20,  5,  29,   True),
    ("1.8", "Final Inspection & Certificate of Occ",15,  5,  30,   True),
]

# Build actual dates from predecessor chain
act_dates = {}   # act_id -> (start_date, finish_date)
for idx, (wbs_id, name, dur, lag, pred, crit) in enumerate(activities_template):
    aid = idx + 1
    if pred is None:
        s = START_DATE
    else:
        s = act_dates[pred][1] + timedelta(days=lag + 1)
    f = s + timedelta(days=dur - 1)
    act_dates[aid] = (s, f)
    schedule_rows.append({
        "Activity_ID":       f"A{aid:03d}",
        "WBS_ID":            wbs_id,
        "Activity_Name":     name,
        "Planned_Start":     s.isoformat(),
        "Planned_Finish":    f.isoformat(),
        "Duration_Days":     dur,
        "Predecessor_Act":   f"A{pred:03d}" if pred else "",
        "Is_Critical_Path":  crit,
        "Float_Days":        0 if crit else random.randint(5, 25),
    })

sched_df = pd.DataFrame(schedule_rows)
sched_df.to_csv(f"{OUTPUT}/schedule.csv", index=False)
print("✓ schedule.csv")

# ── EVM MONTHLY TABLE ────────────────────────────────────────────────────────
# For each work package, distribute BCWS across its active months using an S-curve
# Then simulate realistic BCWP and ACWP with controlled variances

def s_curve_weights(n_periods):
    """Bell-shaped weights that integrate to 1 (S-curve derivative)"""
    x = np.linspace(-2, 2, n_periods)
    w = np.exp(-0.5 * x**2)
    return w / w.sum()

evm_rows = []

# Per-package performance profiles (cost_index, schedule_index, start_drift_months)
# cost_index < 1 means over budget; sched_index < 1 means behind schedule
pkg_profiles = {
    "1.1": (0.97, 1.00,  0),   # Mobilization: slight cost overrun
    "1.2": (0.88, 0.90,  1),   # Foundations: geotechnical surprise — cost & schedule hit
    "1.3": (0.95, 0.93,  1),   # Concrete frame: behind due to foundation delay
    "1.4": (1.02, 0.97,  2),   # Steel: slight cost saving, minor delay
    "1.5": (0.91, 0.85,  3),   # Envelope: curtain wall delivery delay
    "1.6": (0.96, 0.92,  2),   # MEP: coordination rework
    "1.7": (0.98, 0.95,  3),   # Finishes: cascading delay
    "1.8": (1.00, 1.00,  4),   # Closeout: TBD (future)
}

for _, row in wbs_df[wbs_df["WBS_Level"] == 2].iterrows():
    wid     = row["WBS_ID"]
    bac     = row["BAC"]
    ps      = date.fromisoformat(row["Planned_Start"])
    pf      = date.fromisoformat(row["Planned_Finish"])
    ci, si, drift = pkg_profiles[wid]

    # Find which reporting periods are within this package's life
    active = [i for i, pe in enumerate(PERIODS)
              if ps <= pe and pe.replace(day=1) <= pf]
    if not active:
        continue
    n = len(active)
    weights = s_curve_weights(n)

    # BCWS: planned value distributed by S-curve
    bcws_monthly = (weights * bac).round(2)

    # Actual start is drifted by drift months
    actual_start_idx = active[0] + drift
    actual_active = [i for i in range(actual_start_idx,
                                      min(actual_start_idx + n, TOTAL_MONTHS))]
    if not actual_active:
        actual_active = active

    bcwp_monthly_full = (weights * bac * si).round(2)
    acwp_monthly_full = (bcwp_monthly_full / ci).round(2)

    cumulative_bcws = 0
    cumulative_bcwp = 0
    cumulative_acwp = 0

    for period_idx in range(TOTAL_MONTHS):
        period_date = PERIODS[period_idx]
        period_label = period_date.strftime("%Y-%m")

        # BCWS this period
        if period_idx in active:
            local = active.index(period_idx)
            bcws_p = float(bcws_monthly[local])
        else:
            bcws_p = 0.0
        cumulative_bcws += bcws_p

        # BCWP & ACWP this period (actual work lags by drift)
        if period_idx in actual_active:
            local2 = actual_active.index(period_idx)
            if local2 < len(bcwp_monthly_full):
                bcwp_p = float(bcwp_monthly_full[local2])
                acwp_p = float(acwp_monthly_full[local2])
            else:
                bcwp_p = 0.0
                acwp_p = 0.0
        else:
            bcwp_p = 0.0
            acwp_p = 0.0
        cumulative_bcwp += bcwp_p
        cumulative_acwp += acwp_p

        # Only record periods up to current (month 18 = Oct 2024, simulate reporting through M18)
        if period_idx > 17:
            bcws_p = bcwp_p = acwp_p = 0.0
            # Keep cumulative as-is for future periods (blank actuals)
            cumulative_bcwp_rec = cumulative_bcwp if period_idx <= 17 else None
            cumulative_acwp_rec = cumulative_acwp if period_idx <= 17 else None
        else:
            cumulative_bcwp_rec = cumulative_bcwp
            cumulative_acwp_rec = cumulative_acwp

        # EVM derived
        if cumulative_bcwp_rec and cumulative_acwp_rec:
            cpi   = round(cumulative_bcwp_rec / cumulative_acwp_rec, 4) if cumulative_acwp_rec else None
            spi   = round(cumulative_bcwp_rec / cumulative_bcws, 4)     if cumulative_bcws     else None
            cv    = round(cumulative_bcwp_rec - cumulative_acwp_rec, 2)
            sv    = round(cumulative_bcwp_rec - cumulative_bcws, 2)
            eac   = round(bac / cpi, 2)                                 if cpi                 else None
            etc   = round(eac - cumulative_acwp_rec, 2)                 if eac                 else None
            vac   = round(bac - eac, 2)                                 if eac                 else None
            tcpi  = round((bac - cumulative_bcwp_rec) /
                          (bac - cumulative_acwp_rec), 4)               if (bac - cumulative_acwp_rec) else None
        else:
            cpi = spi = cv = sv = eac = etc = vac = tcpi = None

        evm_rows.append({
            "Period":             period_label,
            "Period_Date":        period_date.isoformat(),
            "WBS_ID":             wid,
            "Work_Package":       row["Work_Package"],
            "BAC":                bac,
            "BCWS_Period":        round(bcws_p, 2),
            "BCWP_Period":        round(bcwp_p, 2) if period_idx <= 17 else None,
            "ACWP_Period":        round(acwp_p, 2) if period_idx <= 17 else None,
            "Cumulative_BCWS":    round(cumulative_bcws, 2),
            "Cumulative_BCWP":    cumulative_bcwp_rec,
            "Cumulative_ACWP":    cumulative_acwp_rec,
            "CPI":                cpi,
            "SPI":                spi,
            "CV":                 cv,
            "SV":                 sv,
            "EAC":                eac,
            "ETC":                etc,
            "VAC":                vac,
            "TCPI":               tcpi,
        })

evm_df = pd.DataFrame(evm_rows)
evm_df.to_csv(f"{OUTPUT}/evm_monthly.csv", index=False)
print("✓ evm_monthly.csv")

# ── RISK REGISTER ────────────────────────────────────────────────────────────
risks = [
    ("R001","1.2","Geotechnical","Undisclosed underground obstructions delay piling",
     "High","High","Active","Engage geotechnical consultant; revise pile design",
     450_000, 30,"2023-02-15","2023-04-01","Cost & Schedule","Open"),
    ("R002","1.3","Design","Structural drawing RFI delays concrete pours",
     "Medium","Medium","Active","Expedite RFI response; daily design team calls",
     180_000, 14,"2023-06-01","2023-08-01","Schedule","Open"),
    ("R003","1.4","Procurement","Structural steel delivery lead time extension (supply chain)",
     "High","Medium","Active","Pre-order steel; identify alternate suppliers",
     220_000, 21,"2023-08-01","2023-10-01","Schedule","Open"),
    ("R004","1.5","Procurement","Curtain wall fabrication delay due to overseas manufacturer",
     "High","High","Active","Advance procurement; weekly status calls with vendor",
     380_000, 45,"2023-10-01","2024-01-01","Cost & Schedule","Open"),
    ("R005","1.6","Coordination","MEP clash conflicts require rework after rough-in",
     "Medium","High","Active","Enforce BIM coordination reviews before installation",
     150_000, 10,"2024-01-15","2024-03-01","Cost","Open"),
    ("R006","1.1","Safety","Contaminated soil discovered during site clearing",
     "Low","High","Mitigated","Soil remediation completed; disposed per EPA standards",
     95_000,  7,"2023-01-15","2023-02-28","Cost","Closed"),
    ("R007","1.3","Quality","Concrete compressive strength below spec on Level 3 pour",
     "Low","High","Mitigated","Core sampling and remedial grouting completed",
     60_000,  5,"2023-08-20","2023-09-10","Cost","Closed"),
    ("R008","1.7","Scope","Owner requests additional conference room fit-out (scope creep)",
     "Medium","Medium","Active","Change order submitted; pending owner approval",
     210_000, 12,"2024-06-01","2024-07-15","Cost & Schedule","Open"),
    ("R009","1.8","Regulatory","Certificate of Occupancy delay due to fire marshal backlog",
     "Medium","Low","Watch","Engage fire marshal early; pre-inspection scheduled",
     0,       20,"2024-11-01","2024-12-15","Schedule","Open"),
    ("R010","1.6","Labor","Electrician trade shortage causing resource constraint",
     "Medium","Medium","Active","Engage second electrical subcontractor",
     120_000, 15,"2024-02-01","2024-04-01","Schedule","Open"),
]

risk_df = pd.DataFrame(risks, columns=[
    "Risk_ID","WBS_ID","Category","Description",
    "Probability","Impact","Status","Mitigation",
    "Cost_Exposure_USD","Schedule_Exposure_Days",
    "Identified_Date","Expected_Resolution","Risk_Type","Register_Status"
])
risk_df.to_csv(f"{OUTPUT}/risk_register.csv", index=False)
print("✓ risk_register.csv")

# ── CHANGE ORDER LOG ─────────────────────────────────────────────────────────
cos = [
    ("CO-001","1.2","Geotechnical","Additional piling due to undisclosed obstructions",
     "2023-03-10","2023-04-05","Approved", 412_000, 28,
     "Owner directed","Geotechnical report updated"),
    ("CO-002","1.1","Environmental","Contaminated soil removal and disposal",
     "2023-01-28","2023-02-20","Approved", 88_000,  5,
     "Unforeseen condition","EPA compliance required"),
    ("CO-003","1.3","Design","Revised rebar layout Level 5-8 per structural RFI",
     "2023-09-01","2023-10-01","Approved", 145_000, 10,
     "Design error","Drawing revision R3 issued"),
    ("CO-004","1.4","Procurement","Structural steel escalation — supplier surcharge",
     "2023-10-15","2023-11-10","Approved", 198_000,  0,
     "Market condition","Price escalation clause invoked"),
    ("CO-005","1.5","Design","Curtain wall system upgrade — Owner value engineering",
     "2023-12-01","2024-01-15","Approved", 275_000, 15,
     "Owner requested","Enhanced performance specification"),
    ("CO-006","1.6","Coordination","MEP rerouting due to structural interference",
     "2024-02-10","2024-03-05","Approved", 132_000,  8,
     "Design coordination","BIM clash resolved; reroute approved"),
    ("CO-007","1.7","Scope","Additional executive conference rooms – 3rd floor",
     "2024-06-05", None,       "Pending",  210_000, 12,
     "Owner requested","Awaiting owner approval"),
    ("CO-008","1.3","Quality","Remedial grouting Level 3 slab — low-strength cores",
     "2023-09-05","2023-09-25","Approved",  55_000,  4,
     "Quality nonconformance","Core test results documented"),
    ("CO-009","1.6","Scope","EV charging station rough-in added to parking structure",
     "2024-03-01","2024-04-10","Approved",  78_000,  6,
     "Owner requested","Sustainability initiative"),
    ("CO-010","1.8","Regulatory","Enhanced commissioning per updated GSA requirements",
     "2024-09-01", None,       "Pending",  65_000,  5,
     "Regulatory","New GSA standards effective Q4 2024"),
]

co_df = pd.DataFrame(cos, columns=[
    "CO_Number","WBS_ID","Category","Description",
    "Submitted_Date","Approved_Date","Status",
    "Cost_Impact_USD","Schedule_Impact_Days",
    "Cause","Resolution_Notes"
])
co_df.to_csv(f"{OUTPUT}/change_orders.csv", index=False)
print("✓ change_orders.csv")

# ── PROJECT INFO TABLE ────────────────────────────────────────────────────────
info = {
    "Field": [
        "Project Name","Project ID","Client","Contract Type",
        "Original Contract Value","Approved Changes","Revised Contract Value",
        "Planned Start","Planned Finish","Reporting Through",
        "Project Manager","Controls Analyst","Location"
    ],
    "Value": [
        PROJECT_NAME, PROJECT_ID,
        "U.S. General Services Administration (GSA)",
        "Lump Sum – Design-Bid-Build",
        f"${CONTRACT_VALUE:,.0f}",
        "$1,658,000",
        "$46,658,000",
        START_DATE.isoformat(), END_DATE.isoformat(),
        PERIODS[17].isoformat(),
        "Sarah Mitchell, PMP",
        "Brook Weldegebriel",
        "Washington, DC Metro Area"
    ]
}
pd.DataFrame(info).to_csv(f"{OUTPUT}/project_info.csv", index=False)
print("✓ project_info.csv")

print("\n✅ All CSVs generated successfully.")
print(f"   Output folder: {OUTPUT}")
