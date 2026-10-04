import json
from pathlib import Path
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "overview": "/overview",
    "findings": "/findings",
    "assessments": "/assessments",
    "fusion": "/fusion",
    "evidence": "/evidence",
}

# Entity-specific endpoints
ENTITY_IDS = [f"CSE-{i:03d}" for i in range(1, 31)]

output = {}

def fetch(name, endpoint):
    print(f"Fetching {name}: {endpoint}")
    try:
        with urllib.request.urlopen(BASE_URL + endpoint) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  skipped: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  skipped: {e}")
        return None


# Main endpoints
for name, endpoint in ENDPOINTS.items():
    result = fetch(name, endpoint)
    if result is not None:
        output[name] = result


# Try the remaining backend endpoints
for name, endpoint in {
    "entities": "/entities",
    "expected_evidence": "/expected-evidence",
    "contradictions": "/contradictions",
    "anomalies": "/anomalies",
    "source_records": "/source-records",
    "reports": "/reports",
    "audit": "/audit",
    "validation": "/validation",
}.items():
    result = fetch(name, endpoint)
    if result is not None:
        output[name] = result


# Entity-specific real analytics
output["statistics"] = {}
output["peer_comparison"] = {}
output["history"] = {}
output["lifecycle"] = {}

for entity_id in ENTITY_IDS:
    stats = fetch(
        f"statistics_{entity_id}",
        f"/statistics/{entity_id}"
    )
    if stats is not None:
        output["statistics"][entity_id] = stats

    peer = fetch(
        f"peer_comparison_{entity_id}",
        f"/peer-comparison?entity_id={entity_id}"
    )
    if peer is not None:
        output["peer_comparison"][entity_id] = peer

    history = fetch(
        f"history_{entity_id}",
        f"/history?entity_id={entity_id}"
    )
    if history is not None:
        output["history"][entity_id] = history

    lifecycle = fetch(
        f"lifecycle_{entity_id}",
        f"/lifecycle/{entity_id}"
    )
    if lifecycle is not None:
        output["lifecycle"][entity_id] = lifecycle


# Write snapshot
output_dir = Path("frontend/src/data")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "demo_snapshot.json"

with output_file.open("w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print()
print("===================================")
print("REAL DEMO SNAPSHOT UPDATED")
print("===================================")
print(f"File: {output_file}")
print()
print("Datasets captured:")

for name, data in output.items():
    if isinstance(data, list):
        print(f"  {name}: {len(data)} records")
    elif isinstance(data, dict):
        print(f"  {name}: {len(data)} entries")
    else:
        print(f"  {name}: object")