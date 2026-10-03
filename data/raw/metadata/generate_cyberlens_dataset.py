import csv
import json
import math
import os
import random
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta

SEED = 26157
random.seed(SEED)
OUT = '/mnt/data/cyberlens_dataset'
os.makedirs(OUT, exist_ok=True)

# ----------------------------
# Dataset design choices
# ----------------------------
CSE_COUNT = 30
PERIODS = [
    ('2025-Q3', '2025-07-01', '2025-09-30'),
    ('2025-Q4', '2025-10-01', '2025-12-31'),
    ('2026-Q1', '2026-01-01', '2026-03-31'),
    ('2026-Q2', '2026-04-01', '2026-06-30'),
    ('2026-Q3', '2026-07-01', '2026-09-30'),
    ('2026-Q4', '2026-10-01', '2026-12-31'),
]
# 6 periods chosen for development; this is a dataset-design decision, not an official PS requirement.

sectors = ['Energy', 'Transport', 'Telecom', 'Finance', 'Defence_Support']
regions = ['North', 'South', 'East', 'West', 'Central']
org_types = ['Public_Utility', 'Financial_Institution', 'Telecom_Operator', 'Transport_Operator', 'Strategic_Service']
operational_scales = ['Small', 'Medium', 'Large']
asset_scales = {'Small': (25, 45), 'Medium': (45, 75), 'Large': (75, 115)}
soc_scales = {'Small': 'Lean', 'Medium': 'Standard', 'Large': 'Extended'}
alert_categories = ['Authentication', 'Endpoint', 'Network', 'Cloud_ControlPlane', 'Data_Access', 'Malware_Heuristic', 'Privilege_Change', 'Vulnerability', 'Policy_Deviation', 'Availability']
severities = ['Low', 'Medium', 'High', 'Critical']
asset_types = ['Server', 'Network_Device', 'Endpoint', 'Application', 'Database', 'Cloud_Service', 'Industrial_System']
system_types = ['Identity', 'Core_Network', 'Business_App', 'Database', 'Messaging', 'Operations', 'Public_Facing', 'Industrial_Control']
monitoring_statuses = ['Monitored', 'Partially_Monitored', 'Not_Monitored']
dispositions = ['True_Positive', 'Benign', 'False_Positive', 'Duplicate', 'Informational', 'Policy_Violation']
case_statuses = ['Open', 'Investigating', 'Contained', 'Remediating', 'Closed']
investigation_statuses = ['Open', 'In_Progress', 'Completed', 'Closed']
escalation_levels = ['L1', 'L2', 'L3', 'Management']
scenario_types = [
    'execution_gap_investigation',
    'execution_gap_fast_closure',
    'execution_gap_missing_escalation',
    'execution_gap_template_investigation',
    'execution_gap_monitoring_weakness',
    'negative_space_missing_investigation',
    'negative_space_missing_escalation',
    'negative_space_low_activity',
    'negative_space_monitoring_gap',
    'peer_deviation',
    'historical_deviation',
    'capability_evidence_contradiction',
    'benign_anomaly',
    'multi_signal_condition',
]

# Behavioral profiles are internal generation controls only; labels never enter operational files.
profiles = {
    'stable': {},
    'investigation_gap': {'investigation_rate': -0.24, 'template_rate': 0.03},
    'fast_closure': {'closure_scale': 0.32},
    'missing_escalation': {'escalation_rate': -0.18},
    'template_investigation': {'template_rate': 0.48},
    'monitoring_gap': {'monitoring_scale': 0.65},
    'low_activity': {'alert_scale': 0.25},
    'kpi_contradiction': {'closure_scale': 1.08, 'investigation_rate': -0.15, 'reported_kpi_high': True},
    'historical_shift': {'closure_scale': 0.72, 'investigation_rate': -0.12},
    'benign_anomaly': {'benign_event': True},
    'multi_signal': {'investigation_rate': -0.28, 'escalation_rate': -0.12, 'closure_scale': 0.38, 'monitoring_scale': 0.55, 'alert_scale': 0.68, 'template_rate': 0.22, 'reported_kpi_high': True},
}

# 30 CSEs: enough variation for peer/historical analytics.
cse_rows = []
profile_assignments = {}
for i in range(1, CSE_COUNT + 1):
    scale = random.choice(operational_scales)
    sector = sectors[(i - 1) % len(sectors)]
    region = regions[(i * 3) % len(regions)]
    org = org_types[(i - 1) % len(org_types)]
    cse_id = f'CSE-{i:03d}'
    # Scenario distribution: mostly normal/stable, with several targeted profiles.
    if i in [4, 11]:
        profile = 'multi_signal'
    elif i in [7, 16]:
        profile = 'investigation_gap'
    elif i in [9, 22]:
        profile = 'fast_closure'
    elif i in [12, 25]:
        profile = 'missing_escalation'
    elif i in [6, 19]:
        profile = 'template_investigation'
    elif i in [14, 27]:
        profile = 'monitoring_gap'
    elif i in [5, 24]:
        profile = 'low_activity'
    elif i in [13, 29]:
        profile = 'kpi_contradiction'
    elif i in [3, 21]:
        profile = 'historical_shift'
    elif i in [10, 28]:
        profile = 'benign_anomaly'
    else:
        profile = 'stable'
    profile_assignments[cse_id] = profile
    cse_rows.append({
        'cse_id': cse_id,
        'cse_name': f'Fictional {org.replace("_", " ")} {i:02d}',
        'organization_type': org,
        'sector': sector,
        'region': region,
        'operational_scale': scale,
        'assessment_group': f'{sector}-{scale}',
        'asset_scale': random.randint(*asset_scales[scale]),
        'soc_scale': soc_scales[scale],
    })

# Global periods table (one row per period) and CSE-period assessment table for historical metrics.
period_rows = []
for pid, start, end in PERIODS:
    period_rows.append({'assessment_period': pid, 'period_start': start, 'period_end': end, 'period_type': 'Quarterly', 'data_status': 'Synthetic'} )

# Helpers
def dt_iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S')

def period_dt_bounds(period_id):
    start = next(x[1] for x in PERIODS if x[0] == period_id)
    end = next(x[2] for x in PERIODS if x[0] == period_id)
    s = datetime.fromisoformat(start + 'T00:00:00')
    e = datetime.fromisoformat(end + 'T23:59:59')
    return s, e

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def choose_severity():
    return random.choices(severities, weights=[0.37, 0.39, 0.19, 0.05])[0]

# Assets
asset_rows = []
assets_by_cse = defaultdict(list)
for c in cse_rows:
    n_assets = c['asset_scale']
    for j in range(1, n_assets + 1):
        crit = random.choices(['Low','Medium','High','Critical'], weights=[0.34,0.38,0.21,0.07])[0]
        asset_id = f"{c['cse_id']}-AST-{j:03d}"
        row = {
            'asset_id': asset_id,
            'cse_id': c['cse_id'],
            'asset_type': random.choice(asset_types),
            'system_type': random.choice(system_types),
            'asset_criticality': crit,
            'monitoring_status': random.choice(['Monitored']*4 + ['Partially_Monitored', 'Not_Monitored']),
            'control_association': random.choice(['CTRL-MON-01','CTRL-DET-02','CTRL-IR-03','CTRL-ACC-04','CTRL-VUL-05']),
            'business_criticality': crit,
            'environment': random.choice(['Production','DR','Corporate','Development']),
            'owner_group': random.choice(['SOC','IT_Operations','Network','Application','Infrastructure']),
            'active_status': random.choice(['Active']*9 + ['Retired']),
        }
        asset_rows.append(row)
        assets_by_cse[c['cse_id']].append(row)

# Operational rows
alert_rows = []
inv_rows = []
esc_rows = []
case_rows = []
monitor_rows = []
historical_rows = []
capability_rows = []
kpi_rows = []
evidence_rows = []
control_mapping_rows = []
expected_evidence_rows = []
ground_truth_rows = []

a_seen = set(); i_seen=set(); e_seen=set(); case_seen=set(); m_seen=set(); ev_seen=set()

# Expected evidence definitions are supporting configuration, not operational labels.
expected_defs = [
    ('EXP-001','Critical_Alert','Investigation','Required','Investigation record expected for critical alerts','Investigation_Data'),
    ('EXP-002','Critical_Alert','Escalation','Conditionally_Required','Escalation evidence expected when severity/process conditions require escalation','Escalation_Data'),
    ('EXP-003','Closed_Case','Remediation','Conditionally_Required','Remediation evidence expected when remediation is required','Case_Management_Data'),
    ('EXP-004','Closed_Case','Closure','Required','Closure record expected for closed cases','Case_Management_Data'),
    ('EXP-005','Critical_Asset','Monitoring','Required','Monitoring evidence expected for critical active assets','Monitoring_Data'),
    ('EXP-006','Investigation','Investigation_Evidence','Expected','Investigation evidence expected for completed investigations','Investigation_Data'),
    ('EXP-007','Escalated_Case','Escalation','Required','Escalation record expected when escalation workflow is present','Escalation_Data'),
]
for r in expected_defs:
    expected_evidence_rows.append({
        'expected_evidence_id': r[0], 'object_type': r[1], 'evidence_category': r[2], 'requirement_level': r[3], 'definition': r[4], 'source_dataset': r[5], 'version': '1.0'
    })

# Control/policy mappings
control_defs = [
    ('CTRL-DET-02','Threat Detection','Alert handling and detection coverage'),
    ('CTRL-IR-03','Incident Response','Investigation, escalation, response and remediation'),
    ('CTRL-MON-01','Security Operations','Monitoring and telemetry coverage'),
    ('CTRL-ACC-04','Operational Discipline','Access and privilege-related operational handling'),
    ('CTRL-VUL-05','Cyber Resilience','Vulnerability and remediation evidence'),
    ('CTRL-GOV-06','Governance and Oversight','Reported KPI/capability versus operational evidence'),
]
for cid, fam, desc in control_defs:
    control_mapping_rows.append({'control_id':cid,'capability_family':fam,'mapping_description':desc,'mapping_version':'1.0'})

# Determine base rate by scale
base_alerts = {'Small': 75, 'Medium': 120, 'Large': 190}
profile_ground_truth_map = {}

# Generate CSE-period baselines first.
for cse in cse_rows:
    pid_factor_base = 1.0
    for idx, (pid, pstart, pend) in enumerate(PERIODS):
        profile = profile_assignments[cse['cse_id']]
        p = profiles[profile]
        scale = cse['operational_scale']
        base = base_alerts[scale]
        # normal seasonal variation
        season = [0.96, 1.04, 0.99, 1.08, 1.02, 1.00][idx]
        alert_count = int(base * season * p.get('alert_scale', 1.0) * random.uniform(0.9, 1.1))
        if profile == 'benign_anomaly' and idx == 3:
            alert_count = int(base * 1.75)
        if profile == 'low_activity' and idx >= 2:
            alert_count = int(base * 0.35 * random.uniform(0.9, 1.05))
        if profile == 'historical_shift' and idx >= 4:
            # deliberate but not extreme behavioural shift
            alert_count = int(base * 1.20 * random.uniform(0.95,1.05))
        # expected baseline metrics used for historical support tables
        investigation_rate = clamp(0.74 + random.uniform(-0.06,0.06) + p.get('investigation_rate',0), 0.2, 0.95)
        escalation_rate = clamp(0.14 + random.uniform(-0.03,0.03) + p.get('escalation_rate',0), 0.02, 0.5)
        closure_rate = clamp(0.80 + random.uniform(-0.05,0.05) * 1 + (p.get('closure_scale',1.0)-1.0)*0.35, 0.35, 0.98)
        if profile == 'historical_shift' and idx >= 4:
            closure_rate = clamp(0.55 + random.uniform(-0.03,0.03), 0.35, 0.8)
        monitoring_cov = clamp(0.93 * p.get('monitoring_scale',1.0) + random.uniform(-0.03,0.03), 0.25, 0.99)
        historical_rows.append({
            'historical_record_id': f"HST-{cse['cse_id']}-{pid}",
            'cse_id': cse['cse_id'], 'assessment_period': pid,
            'alert_volume': alert_count,
            'investigation_rate': round(investigation_rate,4),
            'escalation_rate': round(escalation_rate,4),
            'closure_rate': round(closure_rate,4),
            'monitoring_coverage': round(monitoring_cov,4),
            'avg_investigation_minutes': random.randint(120, 420),
            'avg_closure_minutes': random.randint(180, 720),
        })
        capability_rows.append({
            'capability_record_id': f"CAP-{cse['cse_id']}-{pid}", 'cse_id': cse['cse_id'], 'assessment_period': pid,
            'capability_family': random.choice(['Threat Detection','Investigation','Security Operations','Incident Response','Cyber Resilience']),
            'declared_capability': random.choice(['Established','Mature','Managed','Standardized']),
            'evidence_source': random.choice(['Assessment_Submission','SOC_Report','Control_Mapping']),
        })
        kpi_target_closure = random.choice([0.75,0.80,0.85,0.90])
        reported_closure = kpi_target_closure + random.uniform(0.02,0.05) if p.get('reported_kpi_high') else kpi_target_closure + random.uniform(-0.03,0.03)
        kpi_rows.append({
            'kpi_record_id': f"KPI-{cse['cse_id']}-{pid}", 'cse_id':cse['cse_id'], 'assessment_period':pid,
            'kpi_name':'Case_Closure_Rate', 'target_value':round(kpi_target_closure,4),
            'reported_value':round(clamp(reported_closure,0,1),4), 'unit':'ratio', 'evidence_source':'SOC_Report'
        })

# Alerts and related records
for cse in cse_rows:
    profile = profile_assignments[cse['cse_id']]
    p = profiles[profile]
    scale = cse['operational_scale']
    for idx,(pid,pstart,pend) in enumerate(PERIODS):
        # find target volume from history
        hist = next(h for h in historical_rows if h['cse_id']==cse['cse_id'] and h['assessment_period']==pid)
        n_alerts = hist['alert_volume']
        sdt, edt = period_dt_bounds(pid)
        for n in range(n_alerts):
            alert_id = f"ALT-{cse['cse_id']}-{pid.replace('-', '')}-{n+1:05d}"
            sev = choose_severity()
            # Bias some profiles in specific periods to create discoverable evidence patterns.
            if profile in ('missing_escalation','multi_signal') and random.random() < 0.20:
                sev = random.choices(['High','Critical'], weights=[0.55,0.45])[0]
            asset = random.choice(assets_by_cse[cse['cse_id']])
            ts = sdt + timedelta(seconds=random.randint(0, int((edt-sdt).total_seconds())))
            ack_delay = random.randint(1, 60 if sev in ['Low','Medium'] else 180)
            ack_ts = ts + timedelta(minutes=ack_delay)
            # Some alerts remain open/unclosed.
            closure_exists = random.random() < (0.95 if idx < 5 else 0.90)
            closure_ts = None
            if closure_exists:
                base_close = random.randint(20, 720)
                if profile in ('fast_closure','kpi_contradiction','multi_signal') and sev in ('High','Critical') and random.random() < 0.70:
                    base_close = random.randint(5, 35)
                if profile == 'historical_shift' and idx >= 4 and random.random() < 0.35:
                    base_close = random.randint(5, 60)
                closure_ts = ack_ts + timedelta(minutes=base_close)
            investigation_chance = hist['investigation_rate']
            inv_exists = random.random() < investigation_chance
            case_exists = random.random() < (0.38 if sev in ('High','Critical') else 0.22)
            if profile in ('investigation_gap','multi_signal') and sev in ('High','Critical') and random.random() < 0.65:
                inv_exists = False
            if profile == 'low_activity':
                inv_exists = random.random() < 0.55
            investigation_id = None
            case_id = None
            escalation_status = 'Not_Required'
            disposition = random.choice(dispositions)
            alert_status = 'Closed' if closure_exists else random.choice(['Open','In_Progress'])
            if closure_exists and random.random() < 0.07:
                alert_status = 'Closed'
            # Case creation after alert / ack
            case_created_ts = None
            if case_exists:
                case_id = f"CASE-{cse['cse_id']}-{pid.replace('-', '')}-{n+1:05d}"
                case_seen.add(case_id)
                case_created_ts = (ack_ts + timedelta(minutes=random.randint(5, 180)))
                if closure_ts and case_created_ts > closure_ts:
                    case_created_ts = ack_ts + timedelta(minutes=1)
            # Investigation
            if inv_exists:
                investigation_id = f"INV-{cse['cse_id']}-{pid.replace('-', '')}-{n+1:05d}"
                i_seen.add(investigation_id)
                inv_start = ack_ts + timedelta(minutes=random.randint(0, 90))
                inv_dur = random.randint(20, 720)
                if sev == 'Critical': inv_dur = random.randint(60, 600)
                inv_complete = inv_start + timedelta(minutes=inv_dur)
                if closure_ts and inv_complete > closure_ts:
                    # Keep ordering realistic where a closure exists after investigation.
                    closure_ts = inv_complete + timedelta(minutes=random.randint(5,60))
                template = p.get('template_rate', 0.04)
                evidence_count = random.randint(0,6)
                if template > 0.30 and random.random() < 0.85:
                    evidence_count = random.choice([1,1,2])
                root_cause = random.choice(['Yes','No'])
                if sev == 'Critical' and random.random() < 0.70:
                    root_cause = random.choice(['Yes','No'])
                investigation_evidence = 'INV-EVID-'+investigation_id if evidence_count > 0 else None
                inv_rows.append({
                    'investigation_id': investigation_id, 'cse_id': cse['cse_id'], 'assessment_period': pid,
                    'alert_id': alert_id, 'case_id': case_id,
                    'investigation_start': dt_iso(inv_start), 'investigation_completion': dt_iso(inv_complete),
                    'investigation_status': random.choice(investigation_statuses),
                    'investigation_outcome': random.choice(['Benign','Confirmed_Threat','Policy_Violation','No_Threat_Found','Requires_Remediation']),
                    'investigation_evidence': investigation_evidence,
                    'analyst_activity_metadata': random.choice(['Normal_Activity','Detailed_Notes','Template_Like_Notes','Low_Activity','Multiple_Updates']),
                    'evidence_count': evidence_count, 'root_cause_identified': root_cause,
                    'remediation_required': random.choice(['Yes','No']), 'remediation_status': random.choice(['Not_Applicable','Pending','Completed']),
                })
                # Some escalations are valid, some missing for high-risk cases.
                require_esc = sev in ('High','Critical') and random.random() < 0.52
                if profile in ('missing_escalation','multi_signal') and sev in ('High','Critical'):
                    require_esc = True
                if require_esc and random.random() < max(0.05, hist['escalation_rate']):
                    escalation_id = f"ESC-{cse['cse_id']}-{pid.replace('-', '')}-{n+1:05d}"
                    e_seen.add(escalation_id)
                    esc_ts = inv_complete + timedelta(minutes=random.randint(1,120))
                    if closure_ts and esc_ts > closure_ts:
                        closure_ts = esc_ts + timedelta(minutes=random.randint(1,30))
                    esc_rows.append({
                        'escalation_id': escalation_id, 'cse_id': cse['cse_id'], 'assessment_period':pid,
                        'alert_id': alert_id, 'case_id':case_id, 'investigation_id':investigation_id,
                        'escalation_timestamp':dt_iso(esc_ts), 'escalation_level':random.choice(escalation_levels),
                        'escalation_status':random.choice(['Open','Acknowledged','Completed','Closed']),
                        'escalation_outcome':random.choice(['Transferred','Management_Notified','Additional_Review','No_Further_Action'])
                    })
                    escalation_status = 'Escalated'
                else:
                    escalation_status = 'Not_Escalated'
            # Case record if present
            if case_id:
                c_create = case_created_ts or (ack_ts + timedelta(minutes=10))
                # if investigation exists, case lifecycle can include it; otherwise may legitimately be thin.
                case_closed = closure_ts if (closure_ts and random.random() < 0.88) else None
                remediation_status = random.choice(['Not_Applicable','Pending','In_Progress','Completed'])
                if profile in ('multi_signal','investigation_gap') and sev=='Critical' and random.random()<0.6:
                    remediation_status = random.choice(['Pending','Not_Started'])
                response_action = random.choice(['Triage','Containment','Credential_Reset','Patch','Monitoring_Change','No_Action'])
                case_rows.append({
                    'case_id':case_id,'cse_id':cse['cse_id'],'assessment_period':pid,
                    'associated_alerts':alert_id,'case_creation_timestamp':dt_iso(c_create),
                    'case_status':random.choice(case_statuses) if case_closed is None else 'Closed',
                    'case_closure_timestamp':dt_iso(case_closed) if case_closed else None,
                    'case_lifecycle':random.choice(['Standard','Escalation_Review','Remediation_Required','Monitoring_Review','Investigation_Only']),
                    'remediation_status':remediation_status,
                    'case_evidence':f'CASE-EVID-{case_id}' if random.random()<0.78 else None,
                    'investigation_id':investigation_id,'response_action':response_action,
                    'resolution_evidence':f'RESOL-{case_id}' if case_closed and random.random()<0.72 else None,
                })
            # Monitoring evidence per asset-period is generated separately.
            # Alert evidence availability reflects records, not labels.
            evidence_available = 'Yes' if (investigation_id or case_id) else random.choice(['No','Unknown'])
            alert_rows.append({
                'alert_id':alert_id,'cse_id':cse['cse_id'],'assessment_period':pid,'alert_timestamp':dt_iso(ts),
                'alert_category':random.choice(alert_categories),'alert_severity':sev,'alert_status':alert_status,
                'asset_id':asset['asset_id'],'acknowledgement_timestamp':dt_iso(ack_ts),
                'closure_timestamp':dt_iso(closure_ts) if closure_ts else None,'disposition':disposition,
                'escalation_status':escalation_status,'case_id':case_id,
                'source_system':random.choice(['SOC_Queue','Case_Manager','Detection_Workflow']),
                'detection_method':random.choice(['Rule','Behaviour_Analytics','Correlation','Signature','Manual_Referral']),
                'priority':random.choice(['P3','P2','P1','P0']) if sev in ['High','Critical'] else random.choice(['P4','P3','P2']),
                'evidence_available':evidence_available,
            })
            a_seen.add(alert_id)

# Monitoring evidence. Missing rows for some asset-period pairs intentionally create negative space.
for asset in asset_rows:
    cse_id = asset['cse_id']
    profile = profile_assignments[cse_id]
    p = profiles[profile]
    for idx,(pid,_,_) in enumerate(PERIODS):
        # Critical assets usually expected to have evidence; some targeted gaps lack a row entirely.
        critical = asset['asset_criticality'] == 'Critical'
        miss_prob = 0.015
        if critical: miss_prob = 0.03
        if profile == 'monitoring_gap': miss_prob = 0.28 if critical else 0.10
        if profile == 'multi_signal': miss_prob = 0.20 if critical else 0.07
        if profile == 'benign_anomaly': miss_prob = 0.06 if critical else 0.02
        if random.random() < miss_prob:
            continue
        m_id = f"MON-{cse_id}-{pid.replace('-', '')}-{asset['asset_id'].split('-')[-1]}"
        m_seen.add(m_id)
        if profile in ('monitoring_gap','multi_signal'):
            coverage = random.uniform(0.35,0.78) if random.random()<0.60 else random.uniform(0.80,0.96)
        else:
            coverage = random.uniform(0.82,0.99)
        status = 'Monitored' if coverage >= 0.85 else ('Partially_Monitored' if coverage >= 0.5 else 'Not_Monitored')
        telemetry = random.choice(['Available','Intermittent','Unavailable']) if coverage < 0.85 else random.choice(['Available','Available','Intermittent'])
        sdt,edt=period_dt_bounds(pid)
        ev_ts = sdt + timedelta(days=random.randint(1,85), hours=random.randint(0,23))
        monitor_rows.append({
            'monitoring_record_id':m_id,'cse_id':cse_id,'assessment_period':pid,'asset_id':asset['asset_id'],
            'monitoring_status':status,'telemetry_availability':telemetry,'coverage':round(coverage,4),'evidence_timestamp':dt_iso(ev_ts)
        })

# Evidence reference table built from actual source records.
for row in inv_rows:
    if row['investigation_evidence']:
        eid = f"EV-{row['investigation_id']}-01"
        evidence_rows.append({'evidence_record_id':eid,'cse_id':row['cse_id'],'assessment_period':row['assessment_period'],'source_dataset':'investigations','source_record_id':row['investigation_id'],'evidence_type':'investigation_evidence','evidence_reference':row['investigation_evidence'],'evidence_timestamp':row['investigation_completion'],'availability':'Available'})
        ev_seen.add(eid)
for row in case_rows:
    for field, etype in [('case_evidence','case_evidence'),('resolution_evidence','resolution_evidence')]:
        if row[field]:
            eid = f"EV-{row['case_id']}-{etype}"
            # use case closure timestamp when available, otherwise creation
            ts = row['case_closure_timestamp'] or row['case_creation_timestamp']
            evidence_rows.append({'evidence_record_id':eid,'cse_id':row['cse_id'],'assessment_period':row['assessment_period'],'source_dataset':'cases','source_record_id':row['case_id'],'evidence_type':etype,'evidence_reference':row[field],'evidence_timestamp':ts,'availability':'Available'})
            ev_seen.add(eid)
for row in monitor_rows:
    eid=f"EV-{row['monitoring_record_id']}"
    evidence_rows.append({'evidence_record_id':eid,'cse_id':row['cse_id'],'assessment_period':row['assessment_period'],'source_dataset':'monitoring_evidence','source_record_id':row['monitoring_record_id'],'evidence_type':'monitoring_evidence','evidence_reference':row['monitoring_record_id'],'evidence_timestamp':row['evidence_timestamp'],'availability':'Available'})
    ev_seen.add(eid)

# Capability/control mapping support.
for cse in cse_rows:
    for pid,_,_ in PERIODS:
        capability_record = f"CAP-{cse['cse_id']}-{pid}"
        control_id = random.choice([x[0] for x in control_defs])
        control_mapping_rows.append({'control_id':control_id,'capability_family':next(x[1] for x in control_defs if x[0]==control_id),'mapping_description':f'Applies to {cse["sector"]} supervisory assessment evidence','mapping_version':'1.0','cse_id':cse['cse_id'],'assessment_period':pid,'capability_record_id':capability_record})

# Scenario catalogue (validation-only description). Ground truth references actual source IDs.

def pick_alerts(cse_id, pid, count=5, predicate=None):
    rows=[r for r in alert_rows if r['cse_id']==cse_id and r['assessment_period']==pid]
    if predicate: rows=[r for r in rows if predicate(r)]
    random.shuffle(rows)
    return rows[:count]

def first_or_none(seq):
    return seq[0] if seq else None

# Ground truth scenario instances. These are validation labels and never present in operational datasets.
scenario_counter=1

def add_gt(cse, pid, condition, expected_detection, family, evidence_rows_ref):
    global scenario_counter
    scenario_id=f'SCN-{scenario_counter:03d}'; scenario_counter+=1
    refs=[]
    for r in evidence_rows_ref:
        if isinstance(r, str): refs.append(r)
        elif r and 'alert_id' in r: refs.append(r['alert_id'])
        elif r and 'investigation_id' in r: refs.append(r['investigation_id'])
        elif r and 'case_id' in r: refs.append(r['case_id'])
        elif r and 'monitoring_record_id' in r: refs.append(r['monitoring_record_id'])
    ground_truth_rows.append({'scenario_id':scenario_id,'cse_id':cse,'period':pid,'condition_type':condition,'expected_detection':expected_detection,'expected_signal_family':family,'source_record_ids':'|'.join(refs)})

for cse, profile in profile_assignments.items():
    # choose periods for scenario demonstrations
    for pid,_,_ in PERIODS:
        ars=[r for r in alert_rows if r['cse_id']==cse and r['assessment_period']==pid]
        if not ars: continue
        if profile == 'investigation_gap' and pid in ('2026-Q1','2026-Q2'):
            sel=pick_alerts(cse,pid,5,lambda r:r['alert_severity'] in ('High','Critical') and r['case_id'] is not None and r['evidence_available']!='Yes')
            if sel: add_gt(cse,pid,'execution_gap_missing_investigation','Potential investigation weakness','Execution Gap',[x['alert_id'] for x in sel])
        if profile == 'fast_closure' and pid in ('2026-Q1','2026-Q2'):
            sel=pick_alerts(cse,pid,5,lambda r:r['alert_severity'] in ('High','Critical') and r['closure_timestamp'] and (datetime.fromisoformat(r['closure_timestamp'])-datetime.fromisoformat(r['acknowledgement_timestamp'])).total_seconds()/60 < 45)
            if sel: add_gt(cse,pid,'execution_gap_fast_closure','Potential unusually fast closure behaviour','Execution Gap',[x['alert_id'] for x in sel])
        if profile == 'missing_escalation' and pid in ('2026-Q1','2026-Q2'):
            sel=pick_alerts(cse,pid,5,lambda r:r['alert_severity']=='Critical' and r['case_id'] is not None and r['escalation_status']=='Not_Escalated')
            if sel: add_gt(cse,pid,'execution_gap_missing_escalation','Potential missing escalation for critical activity','Execution Gap',[x['alert_id'] for x in sel])
        if profile == 'template_investigation' and pid in ('2026-Q1','2026-Q2'):
            invs=[r for r in inv_rows if r['cse_id']==cse and r['assessment_period']==pid and r['analyst_activity_metadata']=='Template_Like_Notes']
            if invs: add_gt(cse,pid,'execution_gap_template_investigation','Potential repetitive investigation behaviour','Execution Gap',[x['investigation_id'] for x in invs[:5]])
        if profile in ('monitoring_gap','multi_signal') and pid in ('2026-Q1','2026-Q2'):
            critical_assets=[a for a in assets_by_cse[cse] if a['asset_criticality']=='Critical']
            missing=[]
            for a in critical_assets:
                mons=[m for m in monitor_rows if m['asset_id']==a['asset_id'] and m['assessment_period']==pid]
                if not mons: missing.append(a['asset_id'])
                elif mons[0]['coverage']<0.60: missing.append(mons[0]['monitoring_record_id'])
            if missing: add_gt(cse,pid,'negative_space_monitoring_gap','Potential monitoring coverage/evidence gap','Negative Space',missing[:6])
        if profile == 'low_activity' and pid in ('2026-Q1','2026-Q2'):
            add_gt(cse,pid,'negative_space_low_activity','Potentially low operational activity requiring contextual review','Negative Space',[x['alert_id'] for x in ars[:3]])
        if profile == 'kpi_contradiction' and pid in ('2026-Q1','2026-Q2'):
            add_gt(cse,pid,'capability_evidence_contradiction','Potential inconsistency between reported capability/KPI and observed operational evidence','Capability-Evidence Contradiction',[x['alert_id'] for x in ars[:4]])
        if profile == 'historical_shift' and pid == '2026-Q3':
            add_gt(cse,pid,'historical_deviation','Potential period-over-period behaviour change','Historical Comparison',[x['alert_id'] for x in ars[:4]])
        if profile == 'benign_anomaly' and pid == '2026-Q2':
            add_gt(cse,pid,'benign_anomaly','Unusual operational pattern that requires contextual interpretation','Anomaly',[x['alert_id'] for x in ars[:4]])
        if profile == 'multi_signal' and pid == '2026-Q2':
            add_gt(cse,pid,'multi_signal_condition','Multiple converging evidence signals requiring supervisory review','Signal Fusion',[x['alert_id'] for x in ars[:8]])

# Add generic peer comparison targets for a few normal CSEs (deviation is contextual, not automatically bad).
for cse in ['CSE-001','CSE-002','CSE-015']:
    add_gt(cse,'2026-Q2','peer_deviation','Meaningful deviation from comparable entities for contextual review','Peer Comparison',[r['alert_id'] for r in pick_alerts(cse,'2026-Q2',4)])

# Write helpers

def write_csv(name, rows, field_order=None):
    path=os.path.join(OUT,name)
    if field_order is None:
        field_order=list(rows[0].keys()) if rows else []
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=field_order,extrasaction='ignore')
        w.writeheader(); w.writerows(rows)
    return path

files = {}
files['cse_entities.csv']=write_csv('cse_entities.csv',cse_rows)
files['assessment_periods.csv']=write_csv('assessment_periods.csv',period_rows)
files['alerts.csv']=write_csv('alerts.csv',alert_rows)
files['investigations.csv']=write_csv('investigations.csv',inv_rows)
files['escalations.csv']=write_csv('escalations.csv',esc_rows)
files['cases.csv']=write_csv('cases.csv',case_rows)
files['assets.csv']=write_csv('assets.csv',asset_rows)
files['monitoring_evidence.csv']=write_csv('monitoring_evidence.csv',monitor_rows)
files['historical_assessments.csv']=write_csv('historical_assessments.csv',historical_rows)
files['capabilities.csv']=write_csv('capabilities.csv',capability_rows)
files['kpis.csv']=write_csv('kpis.csv',kpi_rows)
files['evidence_records.csv']=write_csv('evidence_records.csv',evidence_rows)
files['control_mappings.csv']=write_csv('control_mappings.csv',control_mapping_rows)
files['expected_evidence.csv']=write_csv('expected_evidence.csv',expected_evidence_rows)
files['ground_truth.csv']=write_csv('ground_truth.csv',ground_truth_rows)

# Scenario catalogue
scenario_catalogue = [
    {'scenario_type':'execution_gap_investigation','description':'Expected investigation activity is absent for selected higher-severity cases/alerts.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'execution_gap_fast_closure','description':'Selected higher-severity alerts have unusually short acknowledgement-to-closure intervals.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'execution_gap_missing_escalation','description':'Selected critical activity has case/investigation evidence but no corresponding escalation record.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'execution_gap_template_investigation','description':'Selected investigations contain repetitive/template-like analyst activity metadata and sparse evidence.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'execution_gap_monitoring_weakness','description':'Monitoring exists but coverage/telemetry is weak for selected assets.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'negative_space_missing_investigation','description':'Required/expected investigation evidence is absent in selected contexts.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'negative_space_missing_escalation','description':'Expected escalation evidence is absent in selected contexts.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'negative_space_low_activity','description':'Operational volume is materially lower than the same entity baseline.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'negative_space_monitoring_gap','description':'Critical assets have missing or weak monitoring evidence.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'peer_deviation','description':'Entity metrics differ materially from comparable CSEs for contextual review.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'historical_deviation','description':'Entity behaviour changes materially relative to its own historical baseline.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'capability_evidence_contradiction','description':'Reported KPI/capability evidence differs from observed operational evidence.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'benign_anomaly','description':'A genuine unusual pattern is present without asserting supervisory failure.','validation_source':'ground_truth.csv','operational_label_embedded':False},
    {'scenario_type':'multi_signal_condition','description':'Multiple independent evidence signals converge on a review area.','validation_source':'ground_truth.csv','operational_label_embedded':False},
]
write_csv('scenario_catalogue.csv', scenario_catalogue)

# Data dictionary: infer from rows + manually describe important fields.
def dtype_for(v):
    if isinstance(v, bool): return 'boolean'
    if isinstance(v, int): return 'integer'
    if isinstance(v, float): return 'decimal'
    return 'string'

data_dict = []
manual_sources = {
    'cse_entities.csv':'PS core design', 'assessment_periods.csv':'CyberLens supporting design',
    'alerts.csv':'PS core data', 'investigations.csv':'PS core data', 'escalations.csv':'PS core data',
    'cases.csv':'PS core data', 'assets.csv':'PS core data', 'monitoring_evidence.csv':'CyberLens supporting data',
    'historical_assessments.csv':'CyberLens supporting data', 'capabilities.csv':'CyberLens supporting data',
    'kpis.csv':'CyberLens supporting data', 'evidence_records.csv':'CyberLens supporting data',
    'control_mappings.csv':'CyberLens supporting data', 'expected_evidence.csv':'CyberLens supporting data',
}
key_meta = {
    'alert_id':('primary key','Unique synthetic alert identifier'), 'cse_id':('foreign key','Links the record to a CSE entity'),
    'assessment_period':('foreign key','Links the record to an assessment period'), 'asset_id':('foreign key','Links an alert/monitoring row to an asset'),
    'investigation_id':('primary key','Unique synthetic investigation identifier'), 'escalation_id':('primary key','Unique synthetic escalation identifier'),
    'case_id':('primary key','Unique synthetic case identifier'), 'monitoring_record_id':('primary key','Unique monitoring evidence record identifier'),
}
for fn in manual_sources:
    with open(os.path.join(OUT,fn),encoding='utf-8') as f:
        rdr=csv.DictReader(f); fields=rdr.fieldnames; first=next(rdr,None)
    for fld in fields:
        val=first.get(fld) if first else ''
        # sample type
        dtype='string'
        if val:
            if fld.endswith('_timestamp'): dtype='datetime'
            elif fld in ('alert_volume','evidence_count','asset_scale'): dtype='integer'
            elif fld in ('investigation_rate','escalation_rate','closure_rate','monitoring_coverage','target_value','reported_value','coverage'): dtype='decimal'
        role, meaning = key_meta.get(fld, ('attribute', f'Field used for {fld.replace("_", " ")} analysis.'))
        nullable = 'Yes' if any((first or {}).get(fld,'') == '' for _ in [0]) else 'No'
        if fld in ('case_id','investigation_id','asset_id','closure_timestamp','case_closure_timestamp','resolution_evidence','case_evidence','investigation_evidence'):
            nullable='Yes'
        allowed = ''
        if fld=='alert_severity': allowed='Low|Medium|High|Critical'
        if fld=='asset_criticality': allowed='Low|Medium|High|Critical'
        if fld=='monitoring_status': allowed='Monitored|Partially_Monitored|Not_Monitored'
        data_dict.append({'dataset':fn,'field':fld,'data_type':dtype,'meaning':meaning,'nullable':nullable,'allowed_values':allowed,'key_role':role,'source_category':manual_sources[fn],'analytical_usage':'Filtering, feature generation, lifecycle/evidence/peer/historical analysis'})
write_csv('data_dictionary.csv', data_dict)

# Manifest
manifest = {
    'dataset_name':'CyberLens Filtered Synthetic SOC/CSE Supervisory Evidence Dataset',
    'dataset_version':'1.0',
    'generation_date':'2026-10-03',
    'generation_seed':SEED,
    'cse_count':len(cse_rows),
    'assessment_period_count':len(PERIODS),
    'period_ids':[p[0] for p in PERIODS],
    'record_counts':{},
    'schema_version':'1.0',
    'operational_data_is_labeled':False,
    'validation_data_separate':True,
    'source_alignment':'PS 26157 + CyberLens PRD dataset-generation design',
    'notes':'Synthetic, fictional, offline-analytics oriented. Operational files do not embed execution_gap, negative_space, risk_score or final supervisory labels.'
}
for fn in list(files.keys()):
    with open(os.path.join(OUT,fn),encoding='utf-8') as f:
        manifest['record_counts'][fn]=max(0,sum(1 for _ in f)-1)
manifest['record_counts']['ground_truth.csv']=len(ground_truth_rows)
manifest['record_counts']['scenario_catalogue.csv']=len(scenario_catalogue)
with open(os.path.join(OUT,'dataset_manifest.json'),'w',encoding='utf-8') as f:
    json.dump(manifest,f,indent=2)

# Data quality test cases separated from normal inference data.
dq_rows=[
    {'test_case_id':'DQ-001','issue_type':'duplicate_record','dataset':'alerts.csv','description':'Duplicate of an existing alert row for pipeline duplicate detection.','included_in_normal_inference':'No'},
    {'test_case_id':'DQ-002','issue_type':'missing_optional_field','dataset':'investigations.csv','description':'Investigation evidence field blank while other investigation fields remain valid.','included_in_normal_inference':'No'},
    {'test_case_id':'DQ-003','issue_type':'inconsistent_timestamp','dataset':'cases.csv','description':'Synthetic test row with case closure timestamp earlier than creation.','included_in_normal_inference':'No'},
    {'test_case_id':'DQ-004','issue_type':'invalid_relationship','dataset':'escalations.csv','description':'Synthetic test row referencing a non-existent investigation ID.','included_in_normal_inference':'No'},
    {'test_case_id':'DQ-005','issue_type':'stale_evidence','dataset':'monitoring_evidence.csv','description':'Synthetic test row with evidence timestamp outside its assessment period.','included_in_normal_inference':'No'},
]
write_csv('data_quality_test_cases.csv',dq_rows)

# Validation
errors=[]
# Primary key uniqueness
for fn, key in [('cse_entities.csv','cse_id'),('alerts.csv','alert_id'),('investigations.csv','investigation_id'),('escalations.csv','escalation_id'),('cases.csv','case_id'),('assets.csv','asset_id'),('monitoring_evidence.csv','monitoring_record_id'),('evidence_records.csv','evidence_record_id')]:
    with open(os.path.join(OUT,fn),encoding='utf-8') as f:
        vals=[r[key] for r in csv.DictReader(f)]
    dup=[k for k,c in Counter(vals).items() if c>1]
    if dup: errors.append(f'{fn}: duplicate PKs {dup[:5]}')

cse_ids={r['cse_id'] for r in cse_rows}; asset_ids={r['asset_id'] for r in asset_rows}; alert_ids={r['alert_id'] for r in alert_rows}; inv_ids={r['investigation_id'] for r in inv_rows}; case_ids={r['case_id'] for r in case_rows}; esc_ids={r['escalation_id'] for r in esc_rows}
for r in alert_rows:
    if r['cse_id'] not in cse_ids: errors.append('alerts broken cse fk')
    if r['asset_id'] not in asset_ids: errors.append('alerts broken asset fk')
    if r['case_id'] and r['case_id'] not in case_ids: errors.append('alerts broken case fk')
for r in inv_rows:
    if r['cse_id'] not in cse_ids or r['alert_id'] not in alert_ids: errors.append('investigation broken alert/cse fk')
    if r['case_id'] and r['case_id'] not in case_ids: errors.append('investigation broken case fk')
for r in esc_rows:
    if r['alert_id'] not in alert_ids or r['investigation_id'] not in inv_ids: errors.append('escalation broken fk')
    if r['case_id'] and r['case_id'] not in case_ids: errors.append('escalation broken case fk')
for r in case_rows:
    if r['cse_id'] not in cse_ids: errors.append('case broken cse fk')
    if r['investigation_id'] and r['investigation_id'] not in inv_ids: errors.append('case broken investigation fk')
for r in monitor_rows:
    if r['asset_id'] not in asset_ids or r['cse_id'] not in cse_ids: errors.append('monitor broken fk')
for r in evidence_rows:
    if r['cse_id'] not in cse_ids: errors.append('evidence broken cse fk')
    if r['source_dataset']=='alerts' and r['source_record_id'] not in alert_ids: errors.append('evidence broken alert ref')
    if r['source_dataset']=='investigations' and r['source_record_id'] not in inv_ids: errors.append('evidence broken investigation ref')
    if r['source_dataset']=='cases' and r['source_record_id'] not in case_ids: errors.append('evidence broken case ref')
    if r['source_dataset']=='monitoring_evidence' and r['source_record_id'] not in {x['monitoring_record_id'] for x in monitor_rows}: errors.append('evidence broken monitoring ref')

# Temporal checks
for r in alert_rows:
    ack=datetime.fromisoformat(r['acknowledgement_timestamp']); alert=datetime.fromisoformat(r['alert_timestamp'])
    if ack < alert: errors.append(f"ack before alert {r['alert_id']}")
    if r['closure_timestamp'] and datetime.fromisoformat(r['closure_timestamp']) < ack: errors.append(f"closure before ack {r['alert_id']}")
for r in inv_rows:
    if datetime.fromisoformat(r['investigation_completion']) < datetime.fromisoformat(r['investigation_start']): errors.append(f"investigation completion before start {r['investigation_id']}")

# Coverage of required domains
expected_files=[
    'cse_entities.csv','assessment_periods.csv','alerts.csv','investigations.csv','escalations.csv','cases.csv','assets.csv','monitoring_evidence.csv',
    'historical_assessments.csv','capabilities.csv','kpis.csv','evidence_records.csv','control_mappings.csv','expected_evidence.csv','ground_truth.csv',
    'data_dictionary.csv','scenario_catalogue.csv','dataset_manifest.json'
]
for fn in expected_files:
    if not os.path.exists(os.path.join(OUT,fn)): errors.append(f'missing {fn}')

# Scenario coverage summary
scenario_counts=Counter(r['condition_type'] for r in ground_truth_rows)
validation_lines=[]
validation_lines.append('CyberLens Dataset Validation Report')
validation_lines.append('=================================')
validation_lines.append(f'CSE count: {len(cse_rows)}')
validation_lines.append(f'Assessment periods: {len(PERIODS)}')
validation_lines.append('')
validation_lines.append('Record counts:')
for fn,cnt in manifest['record_counts'].items(): validation_lines.append(f'  {fn}: {cnt}')
validation_lines.append('')
validation_lines.append('Integrity checks:')
validation_lines.append(f'  Primary key uniqueness: {"PASS" if not any("duplicate PK" in e for e in errors) else "FAIL"}')
validation_lines.append(f'  Foreign key integrity: {"PASS" if not any("broken" in e for e in errors) else "FAIL"}')
validation_lines.append(f'  Temporal consistency: {"PASS" if not any("before" in e for e in errors) else "FAIL"}')
validation_lines.append(f'  Required file set: {"PASS" if not any(e.startswith("missing ") for e in errors) else "FAIL"}')
validation_lines.append('')
validation_lines.append('Ground-truth validation scenario instances:')
for k,v in sorted(scenario_counts.items()): validation_lines.append(f'  {k}: {v}')
validation_lines.append('')
validation_lines.append('Interpretation:')
validation_lines.append('  Operational files are synthetic and unlabeled; the ground_truth.csv file is validation-only.')
validation_lines.append('  The dataset is intentionally varied so anomalies and deviations can be benign, contextual, or supervisory-significant.')
validation_lines.append('')
if errors:
    validation_lines.append('ERRORS:')
    validation_lines.extend(errors[:50])
else:
    validation_lines.append('Result: ALL CORE VALIDATION CHECKS PASSED.')
with open(os.path.join(OUT,'validation_report.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(validation_lines))

# README
readme='''# CyberLens Filtered Synthetic SOC/CSE Dataset\n\nThis dataset is designed for the CyberLens project mapped to Smart India Hackathon Problem Statement 26157 (Supervisory Analytics Tool for SOC Assessment).\n\n## What is included\n\n### Core PS-aligned operational evidence\n- cse_entities.csv\n- alerts.csv\n- investigations.csv\n- escalations.csv\n- cases.csv\n- assets.csv\n\n### CyberLens supporting analytical data\n- assessment_periods.csv\n- monitoring_evidence.csv\n- historical_assessments.csv\n- capabilities.csv\n- kpis.csv\n- evidence_records.csv\n- control_mappings.csv\n- expected_evidence.csv\n\n### Validation-only material\n- ground_truth.csv — DO NOT give this file to CyberLens during normal inference.\n- scenario_catalogue.csv\n- data_quality_test_cases.csv\n- validation_report.txt\n\n### Documentation / generation\n- data_dictionary.csv\n- dataset_manifest.json\n- generate_cyberlens_dataset.py\n\n## Design principle\nOperational data contains evidence, not conclusions. There are no fields such as `risk_score`, `execution_gap=true`, or `negative_space=true` in the core evidence tables. CyberLens should derive signals from the relationships, timing, missingness, baselines, peer context and evidence availability.\n\n## Dataset scale\n- 30 fictional CSEs\n- 6 quarterly assessment periods\n- Tens of thousands of alert records plus linked investigations, escalations and cases\n- Asset and monitoring evidence supporting negative-space and coverage analysis\n\n## Intended analytics\nThe dataset is structured to exercise:\n1. Lifecycle intelligence\n2. Expected evidence comparison\n3. Negative-space detection\n4. Execution-gap detection\n5. Peer comparison\n6. Historical self-benchmarking\n7. Capability/evidence contradiction analysis\n8. Statistical anomaly detection\n9. Isolation Forest or other unsupervised anomaly methods\n10. Supervisory signal fusion\n11. Review prioritization\n12. Explainability and source-record traceability\n\n## Important\nAll records are synthetic and fictional. This dataset does not represent real CSE infrastructure, real credentials, real customers, or real raw telemetry. It is intended for offline prototype development and validation.\n'''
with open(os.path.join(OUT,'README.md'),'w',encoding='utf-8') as f: f.write(readme)

# Zip deliverable
zip_path='/mnt/data/CyberLens_Filtered_Synthetic_Dataset_v1.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for fn in os.listdir(OUT):
        z.write(os.path.join(OUT,fn),arcname=fn)

print(json.dumps({'output_dir':OUT,'zip':zip_path,'record_counts':manifest['record_counts'],'ground_truth_scenarios':len(ground_truth_rows),'errors':errors[:20]},indent=2))
