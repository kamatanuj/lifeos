# LifeOS Dashboard — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a secure, all-in-one personal management application (LifeOS) with 10 functional modules, email reminders, document vault, calendar, reports, and global search — matching the 17 mock screens provided.

**Architecture:** Full-stack web app — React + TypeScript frontend (SPA), FastAPI (Python) backend REST API, PostgreSQL database, S3-compatible file storage for documents, SMTP for email reminders, Redis for background task queue. Dockerized deployment.

**Tech Stack:**
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Recharts + FullCalendar
- Backend: FastAPI + SQLAlchemy + Alembic + Celery (background tasks)
- Database: PostgreSQL 16 + Redis 7
- Auth: JWT + bcrypt + optional TOTP (2FA)
- Storage: MinIO (S3-compatible) for documents
- Email: SMTP (Gmail/GoDaddy)
- Deploy: Docker Compose on VPS

**Repository Structure:**
```
lifeos/
├── frontend/              # React + TypeScript SPA
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Screen-level components (one per screen)
│   │   ├── hooks/         # Custom React hooks
│   │   ├── api/           # API client functions
│   │   ├── context/       # React context (auth, theme)
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # Business logic
│   │   ├── core/          # Config, security, deps
│   │   └── tasks/         # Celery background tasks
│   ├── alembic/           # DB migrations
│   ├── tests/             # Pytest tests
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

**Screen Inventory (17 mock screens → 20 app screens):**

| # | Screen | Mock File | Type |
|---|--------|-----------|------|
| 1 | Login | — (new) | Auth |
| 2 | Register | — (new) | Auth |
| 3 | Dashboard | Neha_lifeos_UI_demo.jpg | Overview |
| 4 | Bill Payments List | bill_payments.jpg | List |
| 5 | New Bill Entry | new_record_entry_bills_payments.jpg | Form |
| 6 | Recurring Obligations List | recurring_obligations.jpg | List |
| 7 | New Obligation Entry | New_entry_recurring_obligations.jpg | Form |
| 8 | Insurance Renewals List | Insurance_rennewals.jpg | List |
| 9 | New Insurance Policy | New Entry_Insurance_rennewals.jpg | Form |
| 10 | Properties List | properties.jpg | List |
| 11 | Add Property | properties_add_record.jpg | Form |
| 12 | Maintenance & Services List | maintenance&services.jpg | List |
| 13 | New Maintenance Record | new_record_maintenance&services.jpg | Form |
| 14 | Health Management | Health_Management.jpg | List |
| 15 | New Health Entry | New_entry_Health_Management.jpg | Form |
| 16 | Document Vault | documentvault.jpg | List |
| 17 | Upload Document | Newentry_documentvault.jpg | Form |
| 18 | Calendar | calender.jpg | Calendar |
| 19 | Reports & Analytics | reports and analytics.jpg | Dashboard |
| 20 | Settings | — (new) | Settings |

---

## Phase 1: Project Setup & Infrastructure (Tasks 1-8)

### Task 1: Initialize project repository and structure

**Objective:** Create the monorepo with frontend and backend folders, git, and base configs.

**Files:**
- Create: `lifeos/` (root)
- Create: `lifeos/frontend/` (React app)
- Create: `lifeos/backend/` (FastAPI app)
- Create: `lifeos/docker-compose.yml`
- Create: `lifeos/.gitignore`
- Create: `lifeos/README.md`

**Steps:**
1. `mkdir -p lifeos/{frontend,backend}` && `cd lifeos && git init`
2. Create `.gitignore` with Python, Node, env, and Docker patterns
3. Create `README.md` with project overview, setup instructions, and tech stack
4. `git add -A && git commit -m "chore: initialize project structure"`

---

### Task 2: Scaffold FastAPI backend

**Objective:** Set up FastAPI with project structure, config, and health endpoint.

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`

**Steps:**
1. Create `requirements.txt` with: fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, pydantic-settings, python-jose, passlib, python-multipart, celery, redis, minio, aiosmtplib, pytest, httpx
2. Create `core/config.py` — Pydantic Settings class reading from env (DATABASE_URL, SECRET_KEY, SMTP_HOST, MINIO_ENDPOINT, etc.)
3. Create `core/database.py` — SQLAlchemy engine, SessionLocal, Base, get_db dependency
4. Create `main.py` — FastAPI app with CORS, health endpoint `GET /api/health` returning `{"status": "ok"}`
5. Verify: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload` → `curl localhost:8000/api/health` returns `{"status":"ok"}`
6. Commit

---

### Task 3: Scaffold React frontend

**Objective:** Set up React + TypeScript + Vite + Tailwind CSS.

**Files:**
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/tailwind.config.js`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`

**Steps:**
1. `cd frontend && npm create vite@latest . -- --template react-ts`
2. `npm install && npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p`
3. Configure Tailwind: content paths, extend theme with LifeOS colors (primary: #1a5276, dark: #0d2745, accent: #3498db)
4. Add Tailwind directives to `index.css`
5. Create `App.tsx` with a placeholder "LifeOS" text and sidebar layout skeleton
6. Install: `npm install react-router-dom axios lucide-react recharts @fullcalendar/core @fullcalendar/react @fullcalendar/daygrid`
7. Verify: `npm run dev` → browser shows "LifeOS" with sidebar
8. Commit

---

### Task 4: Set up Docker Compose for local development

**Objective:** Docker Compose with PostgreSQL, Redis, MinIO, backend, and frontend.

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `backend/entrypoint.sh`

**Steps:**
1. Create `docker-compose.yml` with services: db (postgres:16-alpine), redis (redis:7-alpine), minio (minio/minio), backend (build ./backend), frontend (build ./frontend)
2. Backend Dockerfile: Python 3.11-slim, install requirements, expose 8000
3. Frontend Dockerfile: Node 20, build Vite, serve with nginx
4. `entrypoint.sh`: run alembic migrations then start uvicorn
5. Verify: `docker compose up -d` → all services healthy
6. Commit

---

### Task 5: Set up Alembic migrations

**Objective:** Configure Alembic for database schema management.

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/`

**Steps:**
1. `cd backend && alembic init alembic`
2. Configure `alembic.ini` with database URL from settings
3. Configure `env.py` to import Base and all models, use target_metadata
4. Create initial migration: `alembic revision --autogenerate -m "initial"`
5. Verify: `alembic upgrade head` creates tables
6. Commit

---

### Task 6: Implement User model and authentication

**Objective:** User model with bcrypt password hashing, JWT token generation/verification.

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/core/deps.py`
- Test: `backend/tests/test_auth.py`

**Steps:**
1. Write `models/user.py`: User model (id, email, name, hashed_password, is_active, created_at)
2. Write `core/security.py`: `hash_password()`, `verify_password()`, `create_access_token()`, `decode_token()`
3. Write `schemas/user.py`: UserCreate, UserLogin, UserResponse schemas
4. Write `routers/auth.py`: POST /api/auth/register, POST /api/auth/login (returns JWT), GET /api/auth/me
5. Write `core/deps.py`: `get_current_user` dependency that decodes JWT
6. Write tests: register → login → access /me
7. Run tests: `pytest tests/test_auth.py -v`
8. Commit

---

### Task 7: Implement frontend auth (Login & Register screens)

**Objective:** Login and Register screens matching the mock design, with JWT token storage.

**Files:**
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/pages/Register.tsx`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/context/AuthContext.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Modify: `frontend/src/App.tsx` (add router)

**Steps:**
1. Create `AuthContext` — stores JWT in localStorage, provides user state, login/logout/register functions
2. Create `api/auth.ts` — axios calls to /api/auth/login, /register, /me
3. Create `Login.tsx` — email/password form, "Sign in with Google" button (placeholder), LifeOS branding (blue gradient background, white card, L logo)
4. Create `Register.tsx` — name/email/password/confirm fields, 2FA checkbox
5. Create `ProtectedRoute` — redirects to /login if not authenticated
6. Update `App.tsx` — React Router with routes: /login, /register, / (protected, dashboard)
7. Verify: Login form submits → token stored → redirect to dashboard
8. Commit

---

### Task 8: Build sidebar navigation and app shell

**Objective:** Sidebar with all module links, top bar with search and notifications, content area.

**Files:**
- Create: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/TopBar.tsx`
- Create: `frontend/src/components/AppLayout.tsx`
- Create: `frontend/src/pages/Dashboard.tsx` (placeholder)
- Modify: `frontend/src/App.tsx` (add all routes)

**Steps:**
1. Create `Sidebar.tsx` — dark blue (#0d2745) sidebar with grouped links: Overview (Dashboard, Calendar, Search), Financials (Bills, Obligations, Insurance), Assets (Properties, Maintenance), Personal (Health, Documents), Insights (Reports), System (Settings, Logout). Each link has icon (lucide-react) + text. Active state: blue background + left border.
2. Create `TopBar.tsx` — white bar with page title, search input (opens search page on focus), notification bell with badge count
3. Create `AppLayout.tsx` — flex layout with Sidebar + main content area (TopBar + page content)
4. Create placeholder pages for all routes (Dashboard, Bills, Calendar, etc.)
5. Update `App.tsx` — routes: /dashboard, /bills, /bills/new, /obligations, /obligations/new, /insurance, /insurance/new, /properties, /properties/new, /maintenance, /maintenance/new, /health, /health/new, /documents, /documents/new, /calendar, /search, /reports, /settings
6. Verify: Clicking sidebar links navigates between placeholder pages
7. Commit

---

## Phase 2: Bill Payments Module (Tasks 9-14)

### Task 9: Create Bill model and migrations

**Objective:** Bill model with all fields from the mock screen.

**Files:**
- Create: `backend/app/models/bill.py`
- Modify: `backend/alembic/versions/` (new migration)

**Steps:**
1. Write `models/bill.py`: Bill model with fields: id, user_id (FK), bill_type (enum: electricity, mobile, internet, credit_card, water, gas, other), provider, amount, due_date, payment_method (enum: upi_gpay, upi_phonepe, credit_card, net_banking, auto_pay, cheque, cash), frequency (enum: one_time, monthly, quarterly, half_yearly, yearly), linked_property_id (nullable FK), reminder_days_before (default 3), repeat_until_paid (bool), notes, status (enum: pending, paid, overdue), paid_date, paid_amount, created_at, updated_at
2. Create migration: `alembic revision --autogenerate -m "add bills table"`
3. Run: `alembic upgrade head`
4. Commit

---

### Task 10: Bill CRUD API endpoints

**Objective:** REST API for listing, creating, viewing, updating, and deleting bills.

**Files:**
- Create: `backend/app/schemas/bill.py`
- Create: `backend/app/routers/bills.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_bills.py`

**Steps:**
1. Write `schemas/bill.py`: BillCreate, BillUpdate, BillResponse schemas
2. Write `routers/bills.py`:
   - GET /api/bills — list user's bills (with filters: status, type, date range)
   - POST /api/bills — create bill
   - GET /api/bills/{id} — get bill detail
   - PUT /api/bills/{id} — update bill
   - DELETE /api/bills/{id} — delete bill
   - GET /api/bills/summary — summary stats (total_due, paid_this_month, upcoming, irregularities)
3. Write tests: create bill → list bills → update status to paid → verify summary
4. Run tests: `pytest tests/test_bills.py -v`
5. Commit

---

### Task 11: Bill Payments list screen (frontend)

**Objective:** Bills list screen matching `bill_payments.jpg` mock — summary cards, table with all columns.

**Files:**
- Create: `frontend/src/api/bills.ts`
- Create: `frontend/src/pages/Bills.tsx`
- Create: `frontend/src/components/SummaryCards.tsx` (reusable)
- Create: `frontend/src/components/DataTable.tsx` (reusable)
- Create: `frontend/src/components/Badge.tsx` (reusable: overdue, due, paid, upcoming)

**Steps:**
1. Create `api/bills.ts` — axios functions: listBills, createBill, getBill, updateBill, deleteBill, getBillSummary
2. Create `Badge.tsx` — colored pill badges (red/overdue, orange/due, green/paid, blue/upcoming)
3. Create `SummaryCards.tsx` — grid of stat cards (reusable across modules)
4. Create `DataTable.tsx` — generic table component with sortable columns, hover states
5. Create `Bills.tsx` — 4 summary cards (Total Due, Paid This Month, Upcoming, Irregularities) + table with columns: Bill Type, Provider, Amount, Due Date, Payment Method, Status, View button. "+ New Bill" button in header.
6. Verify: Bills page loads with data from API, badges show correctly
7. Commit

---

### Task 12: New Bill Entry form screen (frontend)

**Objective:** New bill form matching `new_record_entry_bills_payments.jpg` mock.

**Files:**
- Create: `frontend/src/pages/BillNew.tsx`
- Create: `frontend/src/components/FormField.tsx` (reusable: label + input/select/textarea)
- Create: `frontend/src/components/FileUpload.tsx` (reusable drop zone)

**Steps:**
1. Create `FormField.tsx` — reusable component: accepts label, type (text/number/date/select/textarea), options, value, onChange. Focus ring styling.
2. Create `BillNew.tsx` — 2-column grid form with fields: Bill Type (select), Provider (text), Amount (number), Due Date (date), Payment Method (select), Frequency (select), Linked Property (select), Reminder Days Before (number), Notes (textarea), Repeat reminder until paid (checkbox). Back arrow, Save and Cancel buttons.
3. Form validates required fields, posts to API, redirects to bills list on success
4. Verify: Fill form → Save → appears in bills list
5. Commit

---

### Task 13: Bill payment history view

**Objective:** View bill detail with payment history, historical amounts, irregularity flagging.

**Files:**
- Create: `frontend/src/pages/BillDetail.tsx`
- Create: `backend/app/routers/bills.py` (add GET /api/bills/{id}/history)
- Create: `backend/app/models/bill.py` (add BillPayment model for history)

**Steps:**
1. Create `BillPayment` model: id, bill_id (FK), amount, paid_date, payment_method, notes
2. Add GET /api/bills/{id}/history endpoint — returns all BillPayment records
3. Create `BillDetail.tsx` — shows bill info + payment history table (Date, Amount, Method, Notes) + irregularity alert if amount varies >20% from average
4. Add "Mark as Paid" button that creates a BillPayment record
5. Commit

---

### Task 14: Bill reminder backend logic

**Objective:** Background task that checks due bills and sends email reminders.

**Files:**
- Create: `backend/app/tasks/reminders.py`
- Create: `backend/app/services/email.py`
- Create: `backend/app/templates/email/bill_reminder.html`
- Modify: `backend/app/tasks/reminders.py` (Celery beat schedule)

**Steps:**
1. Create `services/email.py` — `send_email(to, subject, html_body)` using aiosmtplib with SMTP config
2. Create `templates/email/bill_reminder.html` — branded HTML email with: bill type, provider, amount, due date, payment method, historical amounts, irregularity warning
3. Create `tasks/reminders.py` — Celery task `check_bill_reminders()` that:
   - Finds bills where due_date - reminder_days_before <= today AND status != paid
   - Sends email reminder
   - If repeat_until_paid, schedules next reminder in 3 days
   - Marks as overdue if past due_date
4. Configure Celery beat: run `check_bill_reminders` daily at 8 AM
5. Test: create bill due tomorrow → run task → verify email sent
6. Commit

---

## Phase 3: Recurring Obligations Module (Tasks 15-18)

### Task 15: Obligation model and API

**Files:**
- Create: `backend/app/models/obligation.py`
- Create: `backend/app/schemas/obligation.py`
- Create: `backend/app/routers/obligations.py`
- Test: `backend/tests/test_obligations.py`

**Steps:**
1. Model: Obligation (id, user_id, name, category enum, amount, frequency, next_due_date, linked_property_id, reminder_days_before, payment_method, repeat_until_completed, send_to_family, is_active, last_paid_date, created_at)
2. Schemas: ObligationCreate, ObligationUpdate, ObligationResponse
3. Router: GET /api/obligations (list + summary stats), POST, GET/{id}, PUT/{id}, DELETE/{id}, POST /api/obligations/{id}/mark-paid (advances next_due_date based on frequency)
4. Tests: CRUD + mark-paid advances date
5. Commit

---

### Task 16: Obligations list and new entry screens (frontend)

**Files:**
- Create: `frontend/src/api/obligations.ts`
- Create: `frontend/src/pages/Obligations.tsx`
- Create: `frontend/src/pages/ObligationNew.tsx`

**Steps:**
1. `api/obligations.ts` — listObligations, createObligation, markObligationPaid, deleteObligation
2. `Obligations.tsx` — 3 summary cards (Active, Monthly Total, Overdue) + table: Obligation, Category, Amount, Frequency, Next Due, Status. "+ New Obligation" button.
3. `ObligationNew.tsx` — form: Name, Category (select), Amount, Frequency (select), First Due Date, Linked Property, Reminder Days Before, Payment Method, Repeat reminder checkbox, Send to family checkbox
4. Verify: Create obligation → appears in list → mark paid → next due advances
5. Commit

---

### Task 17: Obligation reminder integration

**Files:**
- Modify: `backend/app/tasks/reminders.py` (add obligation checks)

**Steps:**
1. Add `check_obligation_reminders()` to tasks — same pattern as bills: find due obligations, send email, repeat if needed, mark overdue
2. Add to Celery beat schedule
3. Test: obligation due tomorrow → run task → email sent
4. Commit

---

### Task 18: Obligation detail view with history

**Files:**
- Create: `backend/app/models/obligation.py` (add ObligationPayment model)
- Create: `frontend/src/pages/ObligationDetail.tsx`

**Steps:**
1. ObligationPayment model: id, obligation_id, amount, paid_date, method
2. API: GET /api/obligations/{id}/history
3. `ObligationDetail.tsx` — obligation info + payment history + "Mark Paid" button
4. Commit

---

## Phase 4: Insurance Module (Tasks 19-22)

### Task 19: Insurance model and API

**Files:**
- Create: `backend/app/models/insurance.py`
- Create: `backend/app/schemas/insurance.py`
- Create: `backend/app/routers/insurance.py`
- Test: `backend/tests/test_insurance.py`

**Steps:**
1. Model: InsurancePolicy (id, user_id, policy_type enum, provider, policy_number, premium_amount, renewal_date, frequency, coverage_amount, linked_property_id, coverage_details, document_id nullable FK, status, created_at)
2. Schemas + Router (CRUD + summary: active count, total premium, renewing soon)
3. Tests
4. Commit

---

### Task 20: Insurance list and new policy screens (frontend)

**Files:**
- Create: `frontend/src/api/insurance.ts`
- Create: `frontend/src/pages/Insurance.tsx`
- Create: `frontend/src/pages/InsuranceNew.tsx`

**Steps:**
1. `Insurance.tsx` — 3 summary cards (Active Policies, Total Premium/Year, Renewing 90 days) + policy cards in 2-column grid: each card shows policy name, provider, policy #, premium, renewal date, status badge, coverage details
2. `InsuranceNew.tsx` — form: Policy Type, Provider, Policy Number, Premium, Renewal Date, Frequency, Coverage Amount, Linked Property, Coverage Details (textarea), Upload Policy Document (file upload → stores in MinIO → links document_id)
3. Commit

---

### Task 21: Insurance renewal reminders

**Files:**
- Modify: `backend/app/tasks/reminders.py`

**Steps:**
1. Add `check_insurance_renewals()` — find policies renewing within reminder_days, send email, repeat until renewed
2. Add to Celery beat
3. Test
4. Commit

---

### Task 22: Insurance detail view

**Files:**
- Create: `frontend/src/pages/InsuranceDetail.tsx`

**Steps:**
1. Show full policy details, premium payment history, linked document (download from MinIO), renewal timeline
2. "Mark Renewed" button → updates renewal_date to next cycle
3. Commit

---

## Phase 5: Properties Module (Tasks 23-28)

### Task 23: Property model and API

**Files:**
- Create: `backend/app/models/property.py`
- Create: `backend/app/schemas/property.py`
- Create: `backend/app/routers/properties.py`
- Test: `backend/tests/test_properties.py`

**Steps:**
1. Model: Property (id, user_id, name, type enum, address, ownership_type enum, purchase_date, society_name, secretary_name, secretary_phone, maintenance_contact, maintenance_phone, insurance_amount, maintenance_amount, society_fee, society_fee_frequency, rental_amount nullable, rental_agreement_expiry nullable, created_at)
2. Schemas + Router (CRUD + list with summary)
3. Tests
4. Commit

---

### Task 24: Property sub-sections (maintenance, tax, insurance, rental)

**Files:**
- Create: `backend/app/models/property.py` (add PropertyMaintenance, PropertyTax, PropertyInsurance, PropertyRental models)
- Create: `backend/app/routers/properties.py` (add sub-resource endpoints)

**Steps:**
1. PropertyMaintenance: property_id, type, description, cost, date, next_due_date, frequency
2. PropertyTax: property_id, year, amount, paid_date, receipt_document_id
3. PropertyInsurance: property_id, provider, policy_number, premium, renewal_date
4. PropertyRental: property_id, tenant_name, rent_amount, agreement_start, agreement_end, document_id
5. API: GET /api/properties/{id}/maintenance, /tax, /insurance, /rental (POST/GET/PUT/DELETE for each)
6. Tests
7. Commit

---

### Task 25: Properties list screen (frontend)

**Files:**
- Create: `frontend/src/api/properties.ts`
- Create: `frontend/src/pages/Properties.tsx`

**Steps:**
1. `Properties.tsx` — 3 property cards in grid. Each card: gradient header with icon, property name, address, badges (Owned/Rented, Society name), footer stats (Insurance, Maintenance/Society fee). "+ Add Property" button.
2. Clicking a card opens property detail (tabs: Profile, Maintenance, Tax, Insurance, Rental)
3. Commit

---

### Task 26: Add Property form screen (frontend)

**Files:**
- Create: `frontend/src/pages/PropertyNew.tsx`

**Steps:**
1. Form matching `properties_add_record.jpg`: Property Name, Type, Address (textarea), Ownership Type, Purchase Date, Society Name, Secretary Name, Secretary Phone, Maintenance Contact, Maintenance Phone
2. Section headers: "Property Profile" and "Society Information"
3. Save → new property card appears in list
4. Commit

---

### Task 27: Property detail screen with tabs

**Files:**
- Create: `frontend/src/pages/PropertyDetail.tsx`
- Create: `frontend/src/components/Tabs.tsx` (reusable)

**Steps:**
1. `Tabs.tsx` — reusable tab component with active underline
2. `PropertyDetail.tsx` — tabs: Profile, Maintenance History, Property Tax, Insurance, Rental Agreement
3. Each tab shows relevant sub-records in table + "Add Record" button
4. Commit

---

### Task 28: Property-linked reminders

**Files:**
- Modify: `backend/app/tasks/reminders.py`

**Steps:**
1. Check property maintenance next_due_date, society fee due dates, property tax due dates, insurance renewal dates
2. Send consolidated property reminders
3. Commit

---

## Phase 6: Maintenance & Services Module (Tasks 29-32)

### Task 29: Maintenance model and API

**Files:**
- Create: `backend/app/models/maintenance.py`
- Create: `backend/app/schemas/maintenance.py`
- Create: `backend/app/routers/maintenance.py`
- Test: `backend/tests/test_maintenance.py`

**Steps:**
1. Model: MaintenanceRecord (id, user_id, type enum, title, property_id nullable, vehicle_id nullable, service_provider, cost, date_completed, next_due_date, frequency, notes, created_at)
2. Schemas + Router (CRUD + summary: due this month, completed YTD, total cost YTD, overdue)
3. Tests
4. Commit

---

### Task 30: Maintenance list and new record screens (frontend)

**Files:**
- Create: `frontend/src/api/maintenance.ts`
- Create: `frontend/src/pages/Maintenance.tsx`
- Create: `frontend/src/pages/MaintenanceNew.tsx`

**Steps:**
1. `Maintenance.tsx` — 4 summary cards + table: Item, Type, Property, Last Done, Next Due, Cost, Status. Matches `maintenance&services.jpg`
2. `MaintenanceNew.tsx` — form matching `new_record_maintenance&services.jpg`: Type (select), Title, Property (select), Service Provider, Cost, Date Completed, Next Due Date, Frequency, Notes (textarea)
3. Commit

---

### Task 31: Car service log with history

**Files:**
- Create: `backend/app/models/maintenance.py` (add ServiceHistory sub-model)
- Create: `frontend/src/pages/MaintenanceDetail.tsx`

**Steps:**
1. ServiceLog: maintenance_id, date, odometer_reading, services_performed, cost, notes
2. `MaintenanceDetail.tsx` — shows record info + service history timeline + add log entry
3. Commit

---

### Task 32: Maintenance reminders

**Files:**
- Modify: `backend/app/tasks/reminders.py`

**Steps:**
1. Check next_due_date for all maintenance records, send reminders 5 days before
2. Commit

---

## Phase 7: Health Management Module (Tasks 33-38)

### Task 33: Health profile models

**Files:**
- Create: `backend/app/models/health.py`
- Test: `backend/tests/test_health.py`

**Steps:**
1. HealthProfile (id, user_id, member_name, relationship enum (self, mother, brother, pet), blood_group, breed nullable for pet, allergies, chronic_conditions, insurance_provider, insurance_number, created_at)
2. HealthRecord (id, profile_id, entry_type enum, date, doctor, hospital, diagnosis, medications, next_appointment, notes, created_at)
3. HealthDocument (id, record_id, document_type, file_path, uploaded_at)
4. Tests
5. Commit

---

### Task 34: Health API

**Files:**
- Create: `backend/app/schemas/health.py`
- Create: `backend/app/routers/health.py`

**Steps:**
1. Profiles: GET /api/health/profiles, POST, PUT, DELETE
2. Records: GET /api/health/profiles/{id}/records, POST, PUT, DELETE
3. Documents: POST /api/health/records/{id}/documents (upload to MinIO), GET documents
4. Summary: GET /api/health/summary — profiles count, active medications, upcoming appointments, recent activity
5. Tests
6. Commit

---

### Task 35: Health Management list screen (frontend)

**Files:**
- Create: `frontend/src/api/health.ts`
- Create: `frontend/src/pages/Health.tsx`

**Steps:**
1. `Health.tsx` — 4 profile cards (Neha, Mom, Darshan, Bruno) with avatar emoji, name, blood group, last visit, alert badge. Matches `Health_Management.jpg`
2. Below cards: "Recent Health Activity" section with timeline of recent records
3. Clicking a profile → Health Profile Detail (tabs: Medical History, Prescriptions, Reports, Doctors)
4. "+ New Entry" button → HealthNew form
5. Commit

---

### Task 36: New Health Entry form screen (frontend)

**Files:**
- Create: `frontend/src/pages/HealthNew.tsx`

**Steps:**
1. Form matching `New_entry_Health_Management.jpg`: Family Member (select), Entry Type (select: Doctor Visit, Prescription, Lab Test, Vaccination, Diagnosis, Surgery, Imaging, Allergy), Date, Doctor, Hospital/Clinic, Next Appointment, Diagnosis/Notes (textarea), Medications Prescribed (textarea), Upload Reports (file drop zone)
2. File upload → MinIO → linked to health record
3. Commit

---

### Task 37: Health profile detail with tabs

**Files:**
- Create: `frontend/src/pages/HealthProfileDetail.tsx`

**Steps:**
1. Tabs: Overview, Medical History, Prescriptions, Reports & Tests, Doctors, Vaccinations
2. Overview: blood group, allergies, chronic conditions, insurance
3. Medical History: timeline of all records
4. Prescriptions: list with medication, dosage, prescribed by, date
5. Reports & Tests: list with document download links
6. Doctors: list with contact info
7. Vaccinations: list with dates and next due
8. Commit

---

### Task 38: Health reminders (appointments, vaccinations, medication refills)

**Files:**
- Modify: `backend/app/tasks/reminders.py`

**Steps:**
1. Check next_appointment dates, vaccination due dates, medication refill dates
2. Send health reminders
3. Bruno's weekly/monthly appointments
4. Commit

---

## Phase 8: Document Vault Module (Tasks 39-43)

### Task 39: Document model and MinIO integration

**Files:**
- Create: `backend/app/models/document.py`
- Create: `backend/app/services/storage.py`
- Test: `backend/tests/test_documents.py`

**Steps:**
1. Document model: id, user_id, name, category enum (insurance, property, identity, medical, tax, bank, warranty, amc, receipt, invoice), linked_type, linked_id, file_path (MinIO key), file_size, mime_type, tags (array), expiry_date nullable, notes, uploaded_at
2. `services/storage.py` — MinIO client: upload_file(file, key) → returns URL, download_file(key) → file stream, delete_file(key)
3. Tests
4. Commit

---

### Task 40: Document API

**Files:**
- Create: `backend/app/schemas/document.py`
- Create: `backend/app/routers/documents.py`

**Steps:**
1. POST /api/documents — multipart upload (file + metadata), stores in MinIO, creates record
2. GET /api/documents — list with filters (category, linked_type, tags, search by name)
3. GET /api/documents/{id} — metadata
4. GET /api/documents/{id}/download — stream file from MinIO
5. PUT /api/documents/{id} — update metadata
6. DELETE /api/documents/{id} — delete from MinIO + DB
7. GET /api/documents/summary — total count, storage used, categories count, expiring soon
8. Tests
9. Commit

---

### Task 41: Document Vault list screen (frontend)

**Files:**
- Create: `frontend/src/api/documents.ts`
- Create: `frontend/src/pages/Documents.tsx`

**Steps:**
1. `Documents.tsx` — 4 summary cards (Total, Storage Used, Categories, Expiring Soon) + category filter pills + table: Document Name (with icon), Category, Linked To, Date, Size, View button. Matches `documentvault.jpg`
2. Clicking filter pill filters by category
3. Clicking View → downloads file
4. "+ Upload Document" button
5. Commit

---

### Task 42: Upload Document form screen (frontend)

**Files:**
- Create: `frontend/src/pages/DocumentNew.tsx`
- Create: `frontend/src/components/FileUpload.tsx` (enhance with progress bar)

**Steps:**
1. Form matching `Newentry_documentvault.jpg`: Drop zone (drag & drop or click), Document Name, Category (select), Linked To (select: properties, health profiles, vehicles), Expiry Date (optional), Tags (comma input), Notes (textarea)
2. Upload progress bar
3. Success → redirect to document list
4. Commit

---

### Task 43: Document expiry reminders

**Files:**
- Modify: `backend/app/tasks/reminders.py`

**Steps:**
1. Check documents with expiry_date approaching (30 days before)
2. Send expiry reminder emails
3. Commit

---

## Phase 9: Calendar Module (Tasks 44-46)

### Task 44: Unified calendar API

**Files:**
- Create: `backend/app/routers/calendar.py`

**Steps:**
1. GET /api/calendar/events?start=YYYY-MM-DD&end=YYYY-MM-DD — aggregates events from all modules:
   - Bills (due_date, type: bill, color: orange)
   - Obligations (next_due_date, type: obligation, color: gray)
   - Insurance (renewal_date, type: insurance, color: blue)
   - Maintenance (next_due_date, type: maintenance, color: green)
   - Health (next_appointment, type: health, color: purple)
   - Documents (expiry_date, type: document, color: red)
2. Each event: id, title, date, type, color, linked_module, linked_id
3. Tests
4. Commit

---

### Task 45: Calendar screen (frontend)

**Files:**
- Create: `frontend/src/api/calendar.ts`
- Create: `frontend/src/pages/Calendar.tsx`

**Steps:**
1. `Calendar.tsx` — monthly calendar view matching `calender.jpg`:
   - 7-column grid (Sun-Sat), day cells with events as colored pills
   - Color legend (Overdue=red, Bills=orange, Insurance=blue, Health=purple, Maintenance=green, Society=gray)
   - Month navigation (‹ ›)
   - Clicking an event → navigates to relevant module detail
2. Use FullCalendar React or custom grid (matching mock style)
3. Commit

---

### Task 46: Calendar event filtering

**Files:**
- Modify: `frontend/src/pages/Calendar.tsx`

**Steps:**
1. Add filter checkboxes: show/hide by category type
2. Add "Today" button to jump to current date
3. Add list view toggle (calendar vs. agenda list)
4. Commit

---

## Phase 10: Reports & Analytics Module (Tasks 47-50)

### Task 47: Reports API

**Files:**
- Create: `backend/app/routers/reports.py`

**Steps:**
1. GET /api/reports/summary?period=YYYY-MM — returns: total_spending, bills_paid, maintenance_cost, health_visits, spending_by_category (array), monthly_trend (6 months array), category_breakdown table
2. GET /api/reports/export?period=YYYY-MM&format=pdf — generates PDF report
3. GET /api/reports/yearly?year=YYYY — annual summary
4. Tests
5. Commit

---

### Task 48: Reports screen with charts (frontend)

**Files:**
- Create: `frontend/src/api/reports.ts`
- Create: `frontend/src/pages/Reports.tsx`

**Steps:**
1. `Reports.tsx` matching `reports and analytics.jpg`:
   - Period selector dropdown (July 2026, June 2026, Last 3 months, YTD)
   - "Export PDF" button
   - 4 summary cards (Total Spending, Bills Paid, Maintenance Cost, Health Visits) with trend indicators
   - 2 charts: Spending by Category (doughnut), Monthly Trend (line) — using Recharts
   - Monthly summary table: Category, Items, Amount, Status
2. Commit

---

### Task 49: PDF export

**Files:**
- Create: `backend/app/services/pdf.py`
- Modify: `backend/app/routers/reports.py`

**Steps:**
1. `services/pdf.py` — use weasyprint or reportlab to generate branded PDF report
2. Report includes: cover page, summary stats, category chart, trend chart, detailed table
3. GET /api/reports/export returns PDF file download
4. Test: generate PDF → verify file is valid PDF
5. Commit

---

### Task 50: Yearly report view

**Files:**
- Create: `frontend/src/pages/Reports.tsx` (add yearly tab)

**Steps:**
1. Add "Monthly" / "Yearly" tab toggle
2. Yearly view: 12-month comparison chart, annual spending by category, property-wise breakdown
3. Commit

---

## Phase 11: Search Module (Tasks 51-52)

### Task 51: Global search API

**Files:**
- Create: `backend/app/routers/search.py`

**Steps:**
1. GET /api/search?q=keyword&category=all — searches across:
   - Bills (provider, type, notes)
   - Obligations (name, category)
   - Insurance (provider, policy_number, type)
   - Properties (name, address, society_name)
   - Maintenance (title, service_provider, notes)
   - Health (doctor, hospital, diagnosis, medications)
   - Documents (name, tags, notes)
2. Returns grouped results by category with relevance
3. Category filter parameter
4. Tests
5. Commit

---

### Task 52: Search screen (frontend)

**Files:**
- Create: `frontend/src/api/search.ts`
- Create: `frontend/src/pages/Search.tsx`

**Steps:**
1. `Search.tsx` — large search input, category filter pills (All, Bills, Properties, Health, Documents, Insurance), results grouped by category
2. Each result shows: title, snippet, category badge, date, click → navigates to detail
3. Empty state: "Start typing to search across all your data..."
4. Debounced search (300ms after typing stops)
5. Commit

---

## Phase 12: Settings & Security (Tasks 53-56)

### Task 53: Settings API

**Files:**
- Create: `backend/app/routers/settings.py`

**Steps:**
1. GET /api/settings — returns user profile, security settings, reminder preferences
2. PUT /api/settings/profile — update name, email, phone
3. PUT /api/settings/password — change password (verify old, hash new)
4. PUT /api/settings/reminders — update reminder frequency, email notifications toggle
5. POST /api/settings/2fa/enable — generate TOTP secret, return QR code
6. POST /api/settings/2fa/verify — verify TOTP code, enable 2FA
7. GET /api/settings/backup — backup status, last backup date
8. POST /api/settings/backup/now — trigger manual backup
9. GET /api/settings/export — export all user data as JSON
10. Tests
11. Commit

---

### Task 54: Settings screen (frontend)

**Files:**
- Create: `frontend/src/api/settings.ts`
- Create: `frontend/src/pages/Settings.tsx`

**Steps:**
1. `Settings.tsx` — 4 cards in 2x2 grid:
   - Profile: Name, Email, Phone, Update button
   - Security: 2FA toggle (green "Enabled" or enable button), Change Password, Encryption status (AES-256 active)
   - Email Reminders: notification toggle, repeat-until-completed toggle, overdue alerts toggle, frequency dropdown
   - Backup & Data: Auto backup status, last backup date, "Backup Now" button, "Export All Data" button
2. Commit

---

### Task 55: 2FA implementation

**Files:**
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/routers/auth.py`
- Create: `frontend/src/pages/TwoFactorVerify.tsx`

**Steps:**
1. Backend: TOTP secret generation, QR code (using pyotp + qrcode), verify endpoint
2. Login flow: if 2FA enabled → after password check, require TOTP code → return JWT
3. Frontend: `TwoFactorVerify.tsx` — 6-digit code input
4. Tests
5. Commit

---

### Task 56: Automated backup system

**Files:**
- Create: `backend/app/tasks/backup.py`
- Create: `backend/app/services/backup.py`

**Steps:**
1. `services/backup.py` — export all user data (DB dump + MinIO files) as encrypted archive
2. `tasks/backup.py` — Celery task running daily at 2 AM, creates encrypted backup, stores in MinIO backup bucket
3. Retention: keep last 30 daily backups
4. Manual backup trigger via API
5. Tests
6. Commit

---

## Phase 13: Dashboard & Integration (Tasks 57-60)

### Task 57: Dashboard API

**Files:**
- Create: `backend/app/routers/dashboard.py`

**Steps:**
1. GET /api/dashboard — returns:
   - Summary cards: due_this_week, total_bills_month, properties_count, health_reminders
   - Upcoming due dates (next 5, sorted by date, with overdue flag)
   - Recent activity (last 5 actions across all modules)
   - Monthly spending chart data (6 months)
   - Reminder distribution chart data (next 30 days, by category)
2. Tests
3. Commit

---

### Task 58: Dashboard screen (frontend)

**Files:**
- Create: `frontend/src/api/dashboard.ts`
- Create: `frontend/src/pages/Dashboard.tsx` (replace placeholder)

**Steps:**
1. `Dashboard.tsx` matching `Neha_lifeos_UI_demo.jpg`:
   - 4 summary cards (Due This Week, Bills Month, Properties, Health Reminders) with icons and colored backgrounds
   - "Upcoming Due Dates" panel — list with colored left borders (red/orange/yellow/blue/purple), badges
   - "Recent Activity" panel — timeline with action icons and dates
   - 2 charts: Monthly Spending (bar), Reminders (doughnut) using Recharts
2. Clicking a due date → navigates to relevant module
3. Auto-refresh every 5 minutes
4. Commit

---

### Task 59: Notification system (frontend)

**Files:**
- Create: `frontend/src/components/Notifications.tsx`
- Create: `backend/app/routers/notifications.py`

**Steps:**
1. Backend: GET /api/notifications — returns unread notifications (overdue items, upcoming reminders, new activity)
2. Frontend: notification dropdown from bell icon in TopBar, badge count, mark as read
3. Poll notifications every 60 seconds
4. Commit

---

### Task 60: Mobile responsive optimization

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx` (collapsible on mobile)
- Modify: `frontend/src/components/AppLayout.tsx` (mobile layout)
- Modify: All page components (responsive grids)

**Steps:**
1. Sidebar: collapsible with hamburger menu on mobile (< 768px), overlay drawer
2. Summary cards: 4 cols → 2 cols → 1 col (responsive breakpoints)
3. Tables: horizontal scroll on mobile, or card view toggle
4. Forms: 2-column → 1-column on mobile
5. Calendar: simplified day cells on mobile
6. Test on 375px (iPhone SE), 768px (iPad), 1280px (desktop)
7. Commit

---

## Phase 14: Testing & Deployment (Tasks 61-65)

### Task 61: Backend integration tests

**Files:**
- Create: `backend/tests/test_integration.py`

**Steps:**
1. Full flow tests: register → login → create property → add bill → mark paid → check dashboard → search → generate report
2. Test reminder system with mock dates
3. Test document upload/download
4. Test 2FA flow
5. Run: `pytest tests/ -v --cov=app`
6. Commit

---

### Task 62: Frontend E2E tests

**Files:**
- Create: `frontend/e2e/tests.spec.ts` (Playwright)

**Steps:**
1. Install Playwright: `npm install -D @playwright/test`
2. Tests: login → navigate all modules → create bill → view dashboard → search → export report
3. Run: `npx playwright test`
4. Commit

---

### Task 63: Production Docker configuration

**Files:**
- Create: `docker-compose.prod.yml`
- Create: `frontend/nginx.conf`
- Modify: `backend/Dockerfile` (production)

**Steps:**
1. Production compose: no volume mounts, environment variables, health checks, restart policies
2. Frontend: build Vite → nginx serve static files with gzip, SPA routing
3. Backend: gunicorn with uvicorn workers, no --reload
4. HTTPS via reverse proxy (nginx or Caddy)
5. Commit

---

### Task 64: Deployment and SSL

**Steps:**
1. Set up VPS (2GB RAM, 50GB SSD)
2. Install Docker + Docker Compose
3. Clone repo, create .env with production values
4. `docker compose -f docker-compose.prod.yml up -d`
5. Set up nginx reverse proxy with Let's Encrypt SSL
6. Configure DNS (lifeos.example.com → VPS IP)
7. Verify: HTTPS works, health endpoint returns ok
8. Commit

---

### Task 65: Documentation and handoff

**Files:**
- Create: `lifeos/README.md` (update with full docs)
- Create: `lifeos/docs/user-guide.md`
- Create: `lifeos/docs/api-reference.md`
- Create: `lifeos/docs/deployment.md`

**Steps:**
1. README: features, tech stack, setup, dev commands
2. User guide: how to use each module, with screenshots
3. API reference: all endpoints with request/response examples
4. Deployment guide: VPS setup, Docker, SSL, backup config
5. Commit

---

## Summary

| Phase | Tasks | Duration | Screens |
|-------|-------|----------|---------|
| 1. Setup & Infrastructure | 1-8 | 3-4 days | Login, Register, Dashboard (shell) |
| 2. Bill Payments | 9-14 | 3-4 days | Bills List, New Bill, Bill Detail |
| 3. Recurring Obligations | 15-18 | 2-3 days | Obligations List, New Obligation, Detail |
| 4. Insurance | 19-22 | 2 days | Insurance List, New Policy, Detail |
| 5. Properties | 23-28 | 4-5 days | Properties List, Add Property, Detail (tabs) |
| 6. Maintenance | 29-32 | 3 days | Maintenance List, New Record, Detail |
| 7. Health Management | 33-38 | 4-5 days | Health List, New Entry, Profile Detail (tabs) |
| 8. Document Vault | 39-43 | 3-4 days | Documents List, Upload Form |
| 9. Calendar | 44-46 | 3 days | Calendar View |
| 10. Reports & Analytics | 47-50 | 3-4 days | Reports (charts + table) |
| 11. Search | 51-52 | 2 days | Search |
| 12. Settings & Security | 53-56 | 3-4 days | Settings, 2FA, Backup |
| 13. Dashboard & Integration | 57-60 | 3-4 days | Dashboard (full), Notifications, Mobile |
| 14. Testing & Deployment | 61-65 | 3-4 days | — |
| **Total** | **65 tasks** | **~42-50 days (6-7 weeks)** | **20 screens** |

---

## Reminder System Summary

The email reminder system (built incrementally in each module) covers:

| Trigger | Email Content | Repeat Logic |
|---------|--------------|--------------|
| Bill due in N days | Bill type, provider, amount, due date, payment method, historical amounts, irregularities | Every 3 days until paid |
| Obligation due in N days | Name, category, amount, due date, payment method | Every 5 days until completed |
| Insurance renewal in 30 days | Policy type, provider, premium, renewal date, coverage | Every 7 days until renewed |
| Maintenance due in 5 days | Item, type, property, estimated cost | Every 7 days until completed |
| Health appointment in 3 days | Member, doctor, hospital, appointment time | Once (plus day-of reminder) |
| Document expiry in 30 days | Document name, category, expiry date | Every 14 days until renewed |
| Overdue items (daily check) | All overdue items consolidated list | Daily until resolved |

All reminders:
- Sent via SMTP email
- Include relevant historical data
- Flag irregularities (amount varies >20% from average)
- Repeat until task is marked complete
- Overdue items get escalated daily

---

## Database Schema Overview

```
users (id, email, name, hashed_password, is_2fa_enabled, totp_secret, created_at)
properties (id, user_id, name, type, address, ownership_type, ...)
bills (id, user_id, bill_type, provider, amount, due_date, payment_method, frequency, linked_property_id, status, ...)
bill_payments (id, bill_id, amount, paid_date, payment_method, notes)
obligations (id, user_id, name, category, amount, frequency, next_due_date, linked_property_id, ...)
obligation_payments (id, obligation_id, amount, paid_date, method)
insurance_policies (id, user_id, policy_type, provider, policy_number, premium_amount, renewal_date, ...)
maintenance_records (id, user_id, type, title, property_id, service_provider, cost, date_completed, next_due_date, ...)
service_logs (id, maintenance_id, date, odometer_reading, services_performed, cost, notes)
health_profiles (id, user_id, member_name, relationship, blood_group, allergies, ...)
health_records (id, profile_id, entry_type, date, doctor, hospital, diagnosis, medications, next_appointment, ...)
documents (id, user_id, name, category, linked_type, linked_id, file_path, file_size, mime_type, tags, expiry_date, ...)
property_maintenance (id, property_id, type, description, cost, date, next_due_date, frequency)
property_tax (id, property_id, year, amount, paid_date, receipt_document_id)
property_insurance (id, property_id, provider, policy_number, premium, renewal_date)
property_rental (id, property_id, tenant_name, rent_amount, agreement_start, agreement_end, document_id)
notifications (id, user_id, type, title, message, linked_module, linked_id, is_read, created_at)
```