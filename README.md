# Database-enabled edition

This project now includes a persistent SQLite database. Start it with `start-database.bat` on Windows or `./start-database.sh` on macOS/Linux. See `DATABASE_SETUP.md` for details.

# Automatic Timetable Scheduling System (ATSS)

A functional academic prototype for managing university timetable data and generating conflict-free class schedules. The project follows the Victoria University case study and provides separate access for administrators, lecturers, and students.

## Victoria University branding

The user interface uses the Victoria University logo supplied in the final-year report and a matching university palette: navy (`#1F2937`), institutional blue (`#315F9F`), light blue (`#669BCF`), and red (`#E2282B`). The Next.js logo is stored in `public/victoria-university-logo.jpeg`. The standalone demonstration embeds the same logo directly so it remains visible when opened offline.

## Included modules

- Secure role-based sign-in for Administrator, Lecturer, and Student
- Dashboard with summary statistics and notifications
- Stock Management workspace with inventory totals, low-stock alerts, search, filters, and add/edit/delete controls
- Faculty, course, module, trimester, lecturer, student, room, and time-slot management
- Lecturer-to-module assignments and student enrolments
- Automatic timetable generation
- Conflict detection for lecturers, rooms, cohorts, and time slots
- Room-capacity checking and lecturer-availability checking
- Lecturer and student personalised timetable views
- Timetable search, printing, and CSV export
- Workload and room-utilisation reports
- SQLite and PostgreSQL/Supabase database schemas, including a dedicated `stock_items` table

## Quickest way to demonstrate the system

Open this file in a modern browser:

```text
standalone-demo/index.html
```

The standalone version does not require installation, internet access, Node.js, or a database. It stores demonstration data in the browser's local storage.

### Demonstration accounts

| Role | Email | Password |
|---|---|---|
| Administrator | admin@vu.ac.ug | admin123 |
| Lecturer | lecturer@vu.ac.ug | lecturer123 |
| Student | student@vu.ac.ug | student123 |

Use the Administrator account to manage records and generate a timetable. Use the Lecturer or Student account to view personalised schedules.

## Running the Next.js application

### Requirements

- Node.js 20 or later
- npm 10 or later

### Installation

From the `ATSS_System` folder, run:

```bash
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

The source application initially uses seeded demonstration data and browser local storage, so it can run before Supabase is connected.

## Supabase/PostgreSQL setup

1. Create a new Supabase project.
2. Open the SQL Editor in Supabase.
3. Run `database/supabase-schema.sql`.
4. Copy `.env.example` to `.env.local`.
5. Add your Supabase project URL and anonymous key.
6. Replace the local-storage provider with Supabase queries when preparing a live deployment.

The supplied schema covers profiles, faculties, trimesters, courses, modules, lecturers, students, rooms, time slots, module assignments, enrolments, timetable entries, notifications, and stock items. It includes primary keys, foreign keys, unique checks, and row-level security foundations.

## Scheduling logic

The timetable generator uses a seeded heuristic and constraint-satisfaction approach. It:

1. Loads modules and lecturer assignments for the selected trimester.
2. Prioritises assignments with fewer lecturer availability options.
3. filters time slots by programme type.
4. filters rooms by expected class size.
5. rejects lecturer, room, cohort, and time-slot clashes.
6. prevents more than two sessions per cohort or lecturer per day.
7. avoids scheduling the same module twice on the same day.
8. scores remaining alternatives and selects among the best candidates using controlled seeded randomisation.
9. returns scheduled entries together with unresolved conflict reports.

Changing the generation seed can produce a different valid arrangement while the same seed reproduces the same result.

## Main project structure

```text
ATSS_System/
├── app/                       Next.js routes and global styles
├── components/                Login, dashboard, CRUD, stock, generation, reports, role views
├── database/
│   ├── atss.sqlite3           Ready-to-use SQLite database
│   ├── sqlite-schema.sql      SQLite schema, including stock_items
│   └── supabase-schema.sql    PostgreSQL/Supabase schema
├── lib/
│   ├── scheduler.ts           Timetable generation and validation engine
│   ├── seed.ts                Demonstration academic data
│   └── types.ts               TypeScript domain models
├── standalone-demo/
│   └── index.html             Immediately runnable offline demonstration
├── .env.example               Environment variable template
└── package.json               Dependencies and scripts
```

## Important deployment notes

This package is a functional academic MVP. Before institutional production use, connect the interfaces to Supabase, enable verified institutional accounts, configure secure password recovery, complete row-level security policies, add audit logs, test with full university data, and deploy behind HTTPS.

## Suggested demonstration sequence

1. Sign in as Administrator.
2. Review faculties, courses, modules, lecturers, students, rooms, and time slots.
3. Open **Stock Management** to add an item, edit quantities, and review low-stock records.
4. Open **Timetable Generation** and generate a schedule.
5. Open **View Timetables** to filter, print, or export the result.
6. Open **Reports** to review lecturer workload and room utilisation.
7. Sign out and sign in as Lecturer or Student to demonstrate personalised access.
