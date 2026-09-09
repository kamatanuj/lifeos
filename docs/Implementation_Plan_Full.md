# LifeOS Dashboard — Implementation Plan

## Hardware Specifications

### Development / Production Server (Single VPS)

| Component | Minimum Spec | Recommended Spec |
|-----------|-------------|-----------------|
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 50 GB SSD | 100 GB NVMe SSD |
| **Bandwidth** | 2 TB/month | 5 TB/month |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| **Backup Storage** | 50 GB external/S3 | 100 GB S3-compatible |

### Why These Specs
- **4 GB RAM minimum:** PostgreSQL (~512MB) + FastAPI (~256MB) + React build (~512MB) + Docker overhead + document processing
- **8 GB recommended:** Headroom for document OCR, PDF generation, multiple concurrent users, backup operations
- **100 GB storage:** Database + encrypted document vault (insurance policies, property papers, medical reports — typically 2-5KB each, but PDFs/photos can be 2-10MB each, expect 5-20GB over 2-3 years)
- **SSD required:** PostgreSQL performance degrades significantly on HDD

### Cloud VPS Options (India)

| Provider | Spec | Monthly Cost |
|----------|------|-------------|
| **Hetzner CX22** | 2 vCPU, 4GB RAM, 40GB SSD | ₹400-500 |
| **Hetzner CX32** | 4 vCPU, 8GB RAM, 80GB SSD | ₹800-1,000 |
| **DigitalOcean** | 2 vCPU, 4GB RAM, 80GB SSD | ₹1,200-1,500 |
| **AWS Lightsail** | 2 vCPU, 4GB RAM, 80GB SSD | ₹1,500-2,000 |
| **Contabo VPS S** | 4 vCPU, 8GB RAM, 100GB SSD | ₹700-900 |

**Recommended: Hetzner CX32 (4 vCPU, 8GB RAM, 80GB SSD) — ₹800-1,000/month**

### Additional Infrastructure

| Service | Purpose | Monthly Cost |
|---------|---------|-------------|
| Domain (d-insights.global already owned) | DNS | ₹0 (existing) |
| Cloudflare (Free plan) | HTTPS, DDoS protection, tunnel | ₹0 |
| Gmail Workspace | Email reminders | ₹200/user |
| S3-compatible storage (MinIO self-hosted or Backblaze B2) | Document vault backup | ₹200-400 |
| Sentry (Free tier) | Error monitoring | ₹0 |
| UptimeRobot (Free tier) | Uptime monitoring | ₹0 |

### Total Monthly Infrastructure Cost: ₹1,200-1,800/month

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Frontend** | React 18 + TypeScript | Component-based, large ecosystem |
| **UI Framework** | Tailwind CSS + shadcn/ui | Rapid UI matching mock screens |
| **Charts** | Recharts | Simple, React-native charts |
| **Calendar** | FullCalendar React | Robust, customizable |
| **State** | Zustand or React Query | Lightweight, server-state caching |
| **Backend** | FastAPI (Python 3.11) | Fast, type-safe, async |
| **ORM** | SQLAlchemy 2.0 + Alembic | Migrations, type safety |
| **Database** | PostgreSQL 16 | Relational, reliable, JSON support |
| **File Storage** | MinIO (self-hosted S3) or local encrypted FS | Document vault |
| **Auth** | JWT + bcrypt + optional TOTP 2FA | Secure, stateless |
| **Email** | aiosmtplib (async SMTP) | Reminder system |
| **Task Queue** | Celery + Redis or APScheduler | Cron jobs for reminders |
| **Containerization** | Docker + Docker Compose | Easy deployment |
| **Reverse Proxy** | Nginx | TLS termination, static files |
| **SSL** | Let's Encrypt / Cloudflare Tunnel | Free HTTPS |

---

## Phase Breakdown

### Phase 1: Foundation & Architecture (Week 1)

**Days 1-2: Project Setup**
- Provision VPS (Hetzner CX32)
- Install Docker, Docker Compose, Nginx
- Set up GitHub repository, CI/CD pipeline
- Create project scaffold (frontend + backend)
- Configure Cloudflare tunnel for HTTPS

**Days 3-4: Database & Auth**
- Design PostgreSQL schema (see below)
- Set up Alembic migrations
- Implement user authentication (register, login, JWT)
- Password hashing (bcrypt)
- Optional 2FA (TOTP) setup
- Session management

**Day 5: API Skeleton**
- FastAPI project structure (routers, models, schemas)
- Base CRUD operations template
- Error handling middleware
- Request validation (Pydantic)
- API documentation (Swagger/OpenAPI auto-generated)

**Database Schema (core tables):**
```
users (id, email, password_hash, name, created_at, 2fa_secret)
properties (id, user_id, name, address, ownership, society_info, secretary_contact, ...)
property_maintenance (id, property_id, type, description, date, status, cost, contact)
property_insurance (id, property_id, policy_no, provider, premium, renewal_date, ...)
property_tax (id, property_id, year, amount, paid_date, receipt_url)
property_rental (id, property_id, tenant, agreement_start, agreement_end, rent, agreement_url)
bills (id, user_id, category, provider, amount, due_date, paid_date, payment_method, property_id, ...)
bill_history (id, bill_id, amount, paid_date, payment_method, notes)
recurring_obligations (id, user_id, title, category, amount, frequency, next_due, completed, ...)
insurance (id, user_id, type, provider, policy_no, premium, renewal_date, coverage, ...)
health_profiles (id, user_id, name, relation, blood_group, allergies, conditions, ...)
health_records (id, profile_id, type, date, doctor, hospital, diagnosis, prescription, report_url, ...)
health_medications (id, profile_id, name, dosage, frequency, start_date, end_date, ...)
documents (id, user_id, title, category, file_path, file_encrypted, metadata_json, uploaded_at)
reminders (id, user_id, module, ref_id, due_date, email_sent, repeat_count, completed, ...)
calendar_events (id, user_id, source_module, source_id, title, date, category, color)
audit_log (id, user_id, action, entity, entity_id, timestamp, details)
```

**Deliverables:**
- Working auth system
- Database schema with migrations
- API skeleton with documentation
- VPS provisioned with Docker
- HTTPS via Cloudflare

---

### Phase 2: Core Modules — Bills, Obligations, Insurance (Week 2)

**Days 1-2: Bill Payments Module**
- Backend: CRUD for bills + bill_history
- Frontend: Bill payments list view (matching mock screen)
  - Table with: category, provider, amount, due date, status
  - Filter by category, property, status
  - Sort by due date
- New bill entry form (matching mock screen)
  - Fields: category, provider, amount, due date, payment method, property, notes
- Payment history view per bill
- Irregularity detection (amount variance > 20% from average)

**Days 3-4: Recurring Obligations Module**
- Backend: CRUD for recurring_obligations
- Frontend: Obligations list view
  - Cards/table with: title, category, amount, frequency, next due, status
  - Overdue highlighting
- New obligation entry form
- Recurring logic: monthly, quarterly, yearly, custom
- "Repeat until completed" flag

**Day 5: Insurance Renewals Module**
- Backend: CRUD for insurance
- Frontend: Insurance list view
  - Cards with: type, provider, policy no, premium, renewal date, days remaining
  - Color-coded urgency (green >30 days, yellow 7-30 days, red <7 days)
- New insurance entry form
- Link to document vault for policy PDF

**Deliverables:**
- 3 working modules with list + form views
- CRUD APIs tested
- UI matching mock screens

---

### Phase 3: Properties & Maintenance (Week 3)

**Days 1-3: Properties Module**
- Backend: CRUD for properties + sub-tables (maintenance, insurance, tax, rental)
- Frontend: Properties list view
  - Property cards with: name, address, thumbnail, key stats
  - Click to expand → full property block
- Property detail view with tabs:
  - Profile (ownership, address, society info, secretary contact)
  - Maintenance (history log, contacts)
  - Insurance (policies linked to insurance module)
  - Property Tax (yearly history)
  - AMC (service contracts)
  - Rental (agreement details, upload agreement copy)
- Add property record form (matching mock screen)
- Link documents from vault

**Days 4-5: Maintenance & Services Module**
- Backend: CRUD for property_maintenance + car service logs
- Frontend: Maintenance list view
  - Filter by property, type (car, property, cleaning), status
  - Service history timeline
- New maintenance entry form
- Car service log: mileage, service type, garage, cost, next due
- Cleaning schedule: recurring schedule per property (Alibag/primary home)

**Deliverables:**
- Full properties module with sub-sections
- Maintenance & services with history logs
- File upload for rental agreements and service receipts

---

### Phase 4: Health Management & Document Vault (Week 4)

**Days 1-3: Health Management Module**
- Backend: CRUD for health_profiles, health_records, health_medications
- Frontend: Health management list view
  - Profile cards for: Neha, Mom, Darshan, Bruno
  - Click profile → detail view with sections:
    - Medical history (diagnoses, surgeries, conditions)
    - Blood group, allergies
    - Medications (current + historical)
    - Vaccinations
    - Doctors & hospitals (contact details)
    - Reports (blood tests, imaging — upload PDF/images)
    - Prescriptions (upload + details)
    - Insurance
- New health record entry form
- File upload for reports and prescriptions

**Days 4-5: Document Vault Module**
- Backend: CRUD for documents + file upload/encryption
- File storage: AES-256 encryption at rest
- Frontend: Document vault list view
  - Grid/list view with: title, category, date, thumbnail
  - Filter by category (insurance, property, identity, medical, tax, bank, warranty, AMC, receipts)
  - Search by title/metadata
- New document entry form
  - Upload file, select category, add metadata tags
  - Link to property/health profile/insurance
- Download with decryption
- Document preview (PDF/image)

**Deliverables:**
- Complete health management with 4 profiles
- Secure document vault with encryption
- File upload/download throughout

---

### Phase 5: Calendar, Reports & Search (Week 5)

**Days 1-2: Calendar Module**
- Backend: Aggregate events from all modules (bills, obligations, insurance, maintenance, health)
- Frontend: FullCalendar integration
  - Month/week/day views
  - Color-coded by category:
    - 🔵 Bills
    - 🟠 Obligations
    - 🟢 Insurance
    - 🔴 Overdue
    - 🟣 Health
    - 🟡 Maintenance
  - Click event → detail popup
  - Filter by category, property
- Auto-generate calendar_events from due dates

**Days 3-4: Reports & Analytics Module**
- Backend: Data aggregation queries
- Frontend: Reports dashboard
  - Monthly summary: total bills paid, upcoming dues, overdue count, document count
  - Yearly summary: expenses by category (pie chart), monthly trends (line chart)
  - Property-wise expense breakdown (bar chart)
  - Health visit frequency
  - Export as PDF
- Charts: Recharts (pie, bar, line, area)

**Day 5: Global Search**
- Backend: Full-text search across all tables (PostgreSQL tsvector)
- Frontend: Search bar in header
  - Instant results dropdown
  - Click result → navigate to module/record
  - Search in: bills, obligations, insurance, properties, health, documents
- Recent searches

**Deliverables:**
- Unified calendar with all due dates
- Reports with charts and PDF export
- Global search across all data

---

### Phase 6: Reminder System & Notifications (Week 6, Days 1-3)

**Days 1-2: Email Reminder Engine**
- APScheduler/Celery cron jobs (daily at 8 AM IST)
- Check all modules for upcoming due dates (7, 3, 1 days before)
- Send email reminders with:
  - Due date
  - How they usually pay (payment method from history)
  - Historical payment amounts
  - Current amount
  - Any irregularities (amount variance)
- Repeat reminders every 3 days until marked completed
- Overdue notifications (daily for overdue items)

**Day 3: Email Templates & Testing**
- HTML email templates (responsive, branded)
- Plain-text fallback
- Test all reminder scenarios
- Unsubscribe/settings page (notification preferences)

**Deliverables:**
- Automated email reminder system
- Repeat-until-completed logic
- Overdue notifications
- Email templates

---

### Phase 7: Security, Polish & Deployment (Week 6, Days 4-6)

**Day 4: Security Hardening**
- AES-256 encryption for document vault (verify)
- Rate limiting on API endpoints
- CSRF protection
- Input sanitization (XSS prevention)
- Optional 2FA enrollment flow
- Password reset via email
- Audit logging (track all data changes)

**Day 5: Backup System**
- Automated daily PostgreSQL dump (encrypted, compressed)
- Document vault backup to S3/Backblaze B2 (daily)
- 30-day retention policy
- Backup verification script (test restore monthly)
- Backup status dashboard

**Day 6: Testing & Deployment**
- Unit tests (pytest for backend, jest for frontend)
- E2E tests (Playwright) for critical flows:
  - Login → create bill → verify reminder
  - Add property → add maintenance record
  - Upload document → download document
  - View calendar → click event
- Production deployment
- Nginx configuration (reverse proxy, static files, gzip)
- Docker Compose production config
- Documentation (README, API docs, user guide)
- Handoff

**Deliverables:**
- Security hardened application
- Automated backup system
- Tested and deployed to production
- Documentation and handoff

---

## Timeline Summary

| Phase | Week | Duration | Focus |
|-------|------|----------|-------|
| 1 | Week 1 | 5 days | Foundation, DB, Auth, API skeleton |
| 2 | Week 2 | 5 days | Bills, Obligations, Insurance |
| 3 | Week 3 | 5 days | Properties, Maintenance & Services |
| 4 | Week 4 | 5 days | Health Management, Document Vault |
| 5 | Week 5 | 5 days | Calendar, Reports, Search |
| 6 | Week 6 | 6 days | Reminders, Security, Backup, Deploy |
| **Total** | **6 weeks** | **31 working days** | **Full production app** |

---

## Cost Summary

### One-Time Development

| Item | Cost |
|------|------|
| Development (6 weeks, full-stack dev) | ₹3,00,000 - ₹3,50,000 |
| UI polish & testing buffer | ₹25,000 - ₹50,000 |
| **Total one-time** | **₹3,25,000 - ₹4,00,000** |

### Monthly Operating Costs

| Item | Cost/month |
|------|-----------|
| Hetzner CX32 VPS (4 vCPU, 8GB RAM) | ₹800 - ₹1,000 |
| Gmail Workspace (1 user) | ₹200 |
| Backblaze B2 backup storage | ₹200 - ₹400 |
| Domain (existing) | ₹0 |
| Cloudflare (free plan) | ₹0 |
| **Total monthly** | **₹1,200 - ₹1,600** |

### First Year Total

| Item | Cost |
|------|------|
| Development (one-time) | ₹3,25,000 - ₹4,00,000 |
| Infrastructure (12 months) | ₹14,400 - ₹19,200 |
| **Year 1 total** | **₹3,39,400 - ₹4,19,200** |

---

## Milestones & Payment Schedule

| Milestone | Deliverable | Payment |
|-----------|-------------|---------|
| M1: Phase 1-2 complete | Auth + Bills + Obligations + Insurance working | 35% |
| M2: Phase 3-4 complete | Properties + Maintenance + Health + Document Vault | 35% |
| M3: Phase 5-6 complete | Calendar + Reports + Search + Reminders + Deploy | 30% |
| **Total** | | **100%** |

---

## Assumptions & Exclusions

### Included
- Single-user application (Neha) with multi-profile support
- All 10 modules as specified
- Email reminder system
- Encrypted document vault
- Calendar, reports, search
- Mobile-responsive web app
- Automated backups
- 6 weeks development
- Deployment to production VPS
- Documentation

### Excluded (future scope)
- Native mobile apps (iOS/Android)
- Bank account integration / auto-import
- Bill scraping from provider websites
- Multi-user collaboration (family member logins)
- SMS/WhatsApp reminders
- AI-powered insights or recommendations
- Mobile push notifications
- Annual maintenance contract (AMC)

### Optional Add-ons (quoted separately)
- Native mobile app (React Native): +3-4 weeks, +₹1.5-2L
- Multi-user with family access: +1 week, +₹35,000
- SMS/WhatsApp reminders: +3 days, +₹15,000 + usage costs
- AMC (annual maintenance): ₹40,000-60,000/year