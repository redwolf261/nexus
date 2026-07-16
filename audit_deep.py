"""
Deep audit of NEXUS output dataset
Validates: campaign_id population, festival_context, FIR narrative diversity, daily_context
"""
import csv
from collections import Counter

# 1. FIR audit
with open('output/firs.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"=== FIR AUDIT ===")
print(f"Total FIRs: {len(rows):,}")

with_campaign = sum(1 for r in rows if r.get('campaign_id', '').strip())
print(f"With campaign_id: {with_campaign:,} ({with_campaign/len(rows)*100:.1f}%)")

with_festival = sum(1 for r in rows if r.get('festival_context', '').strip())
print(f"With festival_context: {with_festival:,} ({with_festival/len(rows)*100:.1f}%)")

# Narrative diversity check
print("\n--- FIR Narrative Diversity (random samples) ---")
import random
random.seed(42)
samples = random.sample(rows, min(10, len(rows)))
for r in samples:
    desc = r['description_en'][:150]
    ct = r['crime_type']
    print(f"  [{ct}] {desc}")
    print()

# 2. daily_context audit
print("=== DAILY CONTEXT AUDIT ===")
with open('output/daily_context.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dc_rows = list(reader)
print(f"Total daily context rows: {len(dc_rows):,}")
print(f"Columns: {list(dc_rows[0].keys())}")
# Show first 3 rows
for r in dc_rows[:3]:
    print(f"  {r}")

# 3. CDR audit
print("\n=== CDR AUDIT ===")
with open('output/cdrs.csv', encoding='utf-8') as f:
    cdrs = list(csv.DictReader(f))
print(f"Total CDRs: {len(cdrs):,}")
print(f"Columns: {list(cdrs[0].keys())}")
if len(cdrs) > 0:
    # Show a sample
    print(f"Sample: {cdrs[0]}")
    # Check for campaign links
    with_campaign = sum(1 for r in cdrs if r.get('linked_campaign_id', '').strip())
    print(f"With linked_campaign_id: {with_campaign:,}")

# 4. Entity resolution audit
print("\n=== ENTITY RESOLUTION AUDIT ===")
with open('output/entity_resolution.csv', encoding='utf-8') as f:
    er = list(csv.DictReader(f))
print(f"Total ER records: {len(er):,}")
if er:
    alias_types = Counter(r.get('alias_type', '') for r in er)
    print(f"Alias types: {dict(alias_types)}")

# 5. Graph connectivity quick check
print("\n=== GRAPH CONNECTIVITY CHECK ===")
entity_types = {
    'firs': len(rows),
    'criminals': sum(1 for _ in open('output/criminals.csv', encoding='utf-8')) - 1,
    'gangs': sum(1 for _ in open('output/gangs.csv', encoding='utf-8')) - 1,
    'vehicles': sum(1 for _ in open('output/vehicles.csv', encoding='utf-8')) - 1,
    'phones': sum(1 for _ in open('output/phones.csv', encoding='utf-8')) - 1,
    'stations': sum(1 for _ in open('output/stations.csv', encoding='utf-8')) - 1,
    'officers': sum(1 for _ in open('output/officers.csv', encoding='utf-8')) - 1,
}
for name, count in entity_types.items():
    print(f"  {name}: {count:,}")

# Check if we have mastermind <-> gang linkage
with open('output/ground_truth_masterminds.csv', encoding='utf-8') as f:
    mms = list(csv.DictReader(f))
for mm in mms:
    gangs = mm.get('controlled_gang_ids', '')
    print(f"  Mastermind {mm['mastermind_id']} ({mm['name_en']}) controls: {gangs}")

print("\n✅ Audit complete")