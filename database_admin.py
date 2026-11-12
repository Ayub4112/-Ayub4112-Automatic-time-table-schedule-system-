#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sqlite3, shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DB = ROOT / "database" / "atss.sqlite3"

def main():
    parser = argparse.ArgumentParser(description="ATSS SQLite database utility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    exp = sub.add_parser("export")
    exp.add_argument("--profile", choices=["standalone", "nextjs"], default="standalone")
    exp.add_argument("--output", default="")
    sub.add_parser("backup")
    args = parser.parse_args()
    if args.command == "status":
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("SELECT profile,version,updated_at,length(data_json) FROM app_state ORDER BY profile").fetchall()
            stock_count = conn.execute("SELECT COUNT(*) FROM stock_items").fetchone()[0]
        for profile, version, updated, size in rows:
            print(f"{profile}: version {version}, {size} bytes, updated {updated}")
        print(f"stock_items: {stock_count} inventory record(s)")
    elif args.command == "export":
        with sqlite3.connect(DB) as conn:
            row = conn.execute("SELECT data_json FROM app_state WHERE profile=?", (args.profile,)).fetchone()
        if not row: raise SystemExit("Profile not found")
        output = Path(args.output) if args.output else ROOT / f"atss-{args.profile}-export.json"
        output.write_text(json.dumps(json.loads(row[0]), indent=2), encoding="utf-8")
        print(output)
    elif args.command == "backup":
        target = ROOT / "database" / f"atss-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite3"
        shutil.copy2(DB, target)
        print(target)

if __name__ == "__main__":
    main()
