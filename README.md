# LifeOS — Personal Management Dashboard

A secure, all-in-one personal management application with 10 functional modules including dashboard, calendar, document vault, email reminders, reports, and global search.

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + Recharts + FullCalendar
- **Backend:** FastAPI + SQLAlchemy + Alembic + Celery (background tasks)
- **Database:** PostgreSQL 16 + Redis 7
- **Auth:** JWT + bcrypt + optional TOTP (2FA)
- **Storage:** MinIO (S3-compatible) for documents
- **Email:** SMTP (Gmail/GoDaddy)
- **Deploy:** Docker Compose on VPS

## Modules

1. Dashboard — Financial overview, upcoming bills, recent activity
2. Calendar — Events, appointments, reminders
3. Search — Global search across all modules
4. Documents — Document vault with categorization
5. Finance — Income/expense tracking, budgets, reports
6. Properties — Property management, maintenance tracking
7. Vehicles — Vehicle records, service history
8. Health — Medical records, prescriptions, appointments
9. Travel — Trip planning, itineraries, expenses
10. Settings — Profile, security, 2FA, preferences

## Design

- **Theme:** Dark navy (#0d2745) sidebar, light background (#f0f2f5), white cards
- **Accent:** Blue (#3498db)
- **Badges:** Red (#e74c3c) overdue, Orange (#f39c12) due, Green (#27ae60) paid, Blue (#3498db) upcoming
- **Font:** Inter

## Status

Currently in prototype phase — `index.html` contains the full interactive HTML mockup with all 10 modules. See `IMPLEMENTATION_PLAN.md` for the complete build plan.

## License

MIT