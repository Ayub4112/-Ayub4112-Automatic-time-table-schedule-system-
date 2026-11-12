# Stock Management Guide

The Administrator account now has a **Stock Management** menu in both the Next.js application and the standalone demonstration.

## Available functions

- Add, edit, and delete inventory items
- Store SKU, item name, category, description, quantity, unit, reorder level, prices, supplier, and storage location
- Increase or reduce quantities from the stock table
- Search by SKU, item name, supplier, or location
- Filter items by category
- View total items, total units, stock value, and low-stock totals
- Identify items that are in stock, low in stock, out of stock, or inactive

## SQLite storage

Inventory data is saved in the dedicated `stock_items` table inside:

```text
database/atss.sqlite3
```

The database server also keeps the stock information synchronized with the application state used by the standalone and Next.js profiles.

## Database endpoints

```text
GET /api/stock
GET /api/state/standalone
POST /api/state/standalone
GET /api/state/nextjs
POST /api/state/nextjs
```

## Opening the system

Run `start-database.bat` on Windows or `./start-database.sh` on macOS/Linux, then log in as Administrator:

```text
Email: admin@vu.ac.ug
Password: admin123
```

Open **Stock Management** from the left navigation menu.
