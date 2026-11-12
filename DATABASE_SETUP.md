# ATSS SQLite Database Edition

This edition stores application data in a real SQLite database instead of relying only on browser Local Storage.

## Start the application

### Windows
Double-click `start-database.bat`.

### macOS or Linux
Run:

```bash
chmod +x start-database.sh
./start-database.sh
```

The application opens at `http://127.0.0.1:8000/`.

## Database location

`database/atss.sqlite3`

The server creates automatic backups inside the database before each update and keeps the 20 latest snapshots for each application profile.

## What is persisted

- Faculties and courses
- Modules and trimesters
- Lecturers and students
- Rooms and timetable inputs
- Module assignments and enrolments
- Generated timetables
- Conflict reports and notifications
- Stock items, quantities, reorder levels, prices, suppliers, and storage locations

## Database API

- `GET /api/health` — server status
- `GET /api/state/standalone` — load standalone application data
- `GET /api/stock` — read the normalized `stock_items` table
- `POST /api/state/standalone` — save standalone application data
- `POST /api/reset/standalone` — reset demonstration data
- `GET /api/export/standalone` — download a JSON backup
- `GET /api/database` — download the SQLite database file

The full Next.js application uses the `nextjs` profile through the same endpoints. Stock changes made in the interface are synchronized with the dedicated SQLite `stock_items` table.

For an existing SQLite installation, run `database/add-stock-table.sql`. New installations already include the table in `database/sqlite-schema.sql`.

## Next.js development mode

1. Start the database service with `python server.py`.
2. In another terminal, install dependencies with `npm install`.
3. Copy `.env.example` to `.env.local`.
4. Run `npm run dev`.
5. Open `http://localhost:3000`.

## Production note

SQLite is suitable for a local installation or a single application server. For a public multi-server deployment, migrate the same data model to Supabase/PostgreSQL using `database/supabase-schema.sql`.
