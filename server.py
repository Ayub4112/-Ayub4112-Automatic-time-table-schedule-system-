#!/usr/bin/env python3
"""ATSS local database server.

Runs with the Python standard library only. It serves the standalone web app and
persists its data in database/atss.sqlite3.
"""
from __future__ import annotations

import json
import mimetypes
import os
import sqlite3
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "atss.sqlite3"
SCHEMA_PATH = DB_DIR / "sqlite-schema.sql"
VALID_PROFILES = {"standalone", "nextjs"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def stock_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "sku": row["sku"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "reorderLevel": row["reorder_level"],
        "unitCost": row["unit_cost"],
        "sellingPrice": row["selling_price"],
        "supplier": row["supplier"],
        "location": row["location"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def get_stock_items(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id,sku,name,category,description,quantity,unit,reorder_level,unit_cost,"
        "selling_price,supplier,location,status,created_at,updated_at "
        "FROM stock_items ORDER BY name COLLATE NOCASE"
    ).fetchall()
    return [stock_row_to_dict(row) for row in rows]


def sync_stock_items(conn: sqlite3.Connection, items: list[dict]) -> None:
    if not isinstance(items, list):
        raise ValueError("stockItems must be an array.")
    ids: list[str] = []
    now = utc_now()
    for raw in items:
        if not isinstance(raw, dict):
            raise ValueError("Each stock item must be an object.")
        item_id = str(raw.get("id", "")).strip()
        sku = str(raw.get("sku", "")).strip().upper()
        name = str(raw.get("name", "")).strip()
        if not item_id or not sku or not name:
            raise ValueError("Every stock item requires an id, SKU, and name.")
        ids.append(item_id)
        status = raw.get("status", "Active")
        if status not in {"Active", "Inactive"}:
            status = "Active"
        created_at = str(raw.get("createdAt") or now)
        updated_at = str(raw.get("updatedAt") or now)
        conn.execute(
            "INSERT INTO stock_items("
            "id,sku,name,category,description,quantity,unit,reorder_level,unit_cost,selling_price,"
            "supplier,location,status,created_at,updated_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "sku=excluded.sku,name=excluded.name,category=excluded.category,description=excluded.description,"
            "quantity=excluded.quantity,unit=excluded.unit,reorder_level=excluded.reorder_level,"
            "unit_cost=excluded.unit_cost,selling_price=excluded.selling_price,supplier=excluded.supplier,"
            "location=excluded.location,status=excluded.status,updated_at=excluded.updated_at",
            (
                item_id,
                sku,
                name,
                str(raw.get("category", "Other")),
                str(raw.get("description", "")),
                max(0, int(float(raw.get("quantity", 0) or 0))),
                str(raw.get("unit", "Pieces")),
                max(0, int(float(raw.get("reorderLevel", 5) or 0))),
                max(0.0, float(raw.get("unitCost", 0) or 0)),
                max(0.0, float(raw.get("sellingPrice", 0) or 0)),
                str(raw.get("supplier", "")),
                str(raw.get("location", "")),
                status,
                created_at,
                updated_at,
            ),
        )
    if ids:
        placeholders = ",".join("?" for _ in ids)
        conn.execute(f"DELETE FROM stock_items WHERE id NOT IN ({placeholders})", ids)
    else:
        conn.execute("DELETE FROM stock_items")


def initialize_database() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for profile in sorted(VALID_PROFILES):
            seed_path = DB_DIR / f"{profile}-seed.json"
            seed = json.loads(seed_path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR IGNORE INTO app_state(profile,data_json,version,updated_at) VALUES(?,?,1,?)",
                (profile, json.dumps(seed, separators=(",", ":")), utc_now()),
            )
        stock_count = conn.execute("SELECT COUNT(*) FROM stock_items").fetchone()[0]
        if stock_count == 0:
            seed = json.loads((DB_DIR / "nextjs-seed.json").read_text(encoding="utf-8"))
            sync_stock_items(conn, seed.get("stockItems", []))
        conn.commit()


def get_state(profile: str) -> dict:
    with connect() as conn:
        row = conn.execute(
            "SELECT profile,data_json,version,updated_at FROM app_state WHERE profile=?", (profile,)
        ).fetchone()
        if not row:
            raise KeyError(profile)
        data = json.loads(row["data_json"])
        data["stockItems"] = get_stock_items(conn)
        return {
            "profile": row["profile"],
            "data": data,
            "version": row["version"],
            "updatedAt": row["updated_at"],
            "database": str(DB_PATH.relative_to(BASE_DIR)),
        }


def save_state(profile: str, data: dict, reason: str = "application save") -> dict:
    if not isinstance(data, dict):
        raise ValueError("The data payload must be a JSON object.")
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    with connect() as conn:
        current = conn.execute(
            "SELECT data_json,version FROM app_state WHERE profile=?", (profile,)
        ).fetchone()
        if current:
            conn.execute(
                "INSERT INTO state_backups(profile,data_json,reason,created_at) VALUES(?,?,?,?)",
                (profile, current["data_json"], reason, utc_now()),
            )
            version = int(current["version"]) + 1
        else:
            version = 1
        conn.execute(
            "INSERT INTO app_state(profile,data_json,version,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(profile) DO UPDATE SET data_json=excluded.data_json, version=excluded.version, updated_at=excluded.updated_at",
            (profile, encoded, version, utc_now()),
        )
        if "stockItems" in data:
            sync_stock_items(conn, data["stockItems"])
        conn.execute(
            "INSERT INTO audit_log(profile,action,details_json,created_at) VALUES(?,?,?,?)",
            (profile, "save", json.dumps({"version": version, "bytes": len(encoded)}), utc_now()),
        )
        # Retain the 20 latest automatic backups per profile.
        conn.execute(
            "DELETE FROM state_backups WHERE profile=? AND id NOT IN "
            "(SELECT id FROM state_backups WHERE profile=? ORDER BY id DESC LIMIT 20)",
            (profile, profile),
        )
        conn.commit()
    return get_state(profile)


def reset_state(profile: str) -> dict:
    seed = json.loads((DB_DIR / f"{profile}-seed.json").read_text(encoding="utf-8"))
    result = save_state(profile, seed, reason="reset to seed")
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(profile,action,details_json,created_at) VALUES(?,?,?,?)",
            (profile, "reset", json.dumps({"version": result["version"]}), utc_now()),
        )
        conn.commit()
    return result


class ATSSHandler(SimpleHTTPRequestHandler):
    server_version = "ATSSDatabaseServer/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/standalone-demo/index.html")
            self.end_headers()
            return
        if path == "/api/health":
            with connect() as conn:
                stock_count = conn.execute("SELECT COUNT(*) FROM stock_items").fetchone()[0]
            self.send_json({"ok": True, "database": str(DB_PATH), "profiles": sorted(VALID_PROFILES), "stockItems": stock_count})
            return
        if path == "/api/stock":
            with connect() as conn:
                self.send_json({"items": get_stock_items(conn)})
            return
        if path.startswith("/api/state/"):
            profile = path.rsplit("/", 1)[-1]
            if profile not in VALID_PROFILES:
                self.send_json({"error": "Unknown profile"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json(get_state(profile))
            return
        if path.startswith("/api/export/"):
            profile = path.rsplit("/", 1)[-1]
            if profile not in VALID_PROFILES:
                self.send_json({"error": "Unknown profile"}, HTTPStatus.NOT_FOUND)
                return
            payload = json.dumps(get_state(profile)["data"], indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="atss-{profile}-backup.json"')
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if path == "/api/database":
            if not DB_PATH.exists():
                self.send_json({"error": "Database not found"}, HTTPStatus.NOT_FOUND)
                return
            payload = DB_PATH.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/vnd.sqlite3")
            self.send_header("Content-Disposition", 'attachment; filename="atss.sqlite3"')
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/state/"):
            profile = path.rsplit("/", 1)[-1]
            if profile not in VALID_PROFILES:
                self.send_json({"error": "Unknown profile"}, HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                payload = json.loads(body.decode("utf-8")) if body else {}
                data = payload.get("data", payload)
                result = save_state(profile, data)
                self.send_json({"ok": True, **result})
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self.send_json({"error": f"Database save failed: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if path.startswith("/api/reset/"):
            profile = path.rsplit("/", 1)[-1]
            if profile not in VALID_PROFILES:
                self.send_json({"error": "Unknown profile"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, **reset_state(profile)})
            return
        self.send_json({"error": "Endpoint not found"}, HTTPStatus.NOT_FOUND)

    def send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    initialize_database()
    host = os.getenv("ATSS_HOST", "127.0.0.1")
    port = int(os.getenv("ATSS_PORT", "8000"))
    url = f"http://{host}:{port}/"
    server = ThreadingHTTPServer((host, port), ATSSHandler)
    print("\nATSS database server is running")
    print(f"Application: {url}")
    print(f"SQLite file: {DB_PATH}")
    print("Press Ctrl+C to stop the server.\n")
    if os.getenv("ATSS_NO_BROWSER") != "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ATSS database server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
