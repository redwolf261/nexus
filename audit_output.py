"""Quick audit of output CSV files"""
import csv, os, glob
from pathlib import Path

output_dir = Path("output")
csv_files = sorted(glob.glob(str(output_dir / "*.csv")))

print(f"{'File':40s} {'Rows':>10s}  {'Cols':>5s}")
print("-" * 58)
for f in csv_files:
    try:
        with open(f, encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            row_count = sum(1 for _ in fh)
            print(f"{os.path.basename(f):40s} {row_count:>10,}  {len(header):>5d}")
    except Exception as e:
        print(f"{os.path.basename(f):40s} {'ERROR':>10s}  {str(e):>30s}")

# Also check for daily_context.csv
dc = output_dir / "daily_context.csv"
if dc.exists():
    rows = sum(1 for _ in open(dc, encoding="utf-8"))
    print(f"\n{os.path.basename(dc)} exists with {rows:,} rows")
else:
    print(f"\n⚠️  daily_context.csv NOT FOUND in output/")