# LifeOS — Knowledge Base Document (for ElevenLabs Agents)

**Purpose:** This document is the knowledge base for an ElevenLabs voice agent representing LifeOS (https://lifeos.converso.work). It describes what LifeOS is, every feature it offers, the voice tools available, and how the agent should answer user questions. Everything here is verified against the live system as of September 10, 2026.

---

## 1. What is LifeOS?

LifeOS is a personal life-management web application. It is a single dashboard where a household manages everything from bills and recurring payments to properties, insurance, health records, and documents — and it is fully **voice-controllable**: every screen can be opened, read, filled, and acted on by speaking to the voice assistant.

- **Website:** https://lifeos.converso.work
- **Primary user:** Anuj Kamat (admin account)
- **Built as:** FastAPI backend + single-page frontend, PostgreSQL database, and a Dograh-powered voice agent that talks to the app's APIs in real time.
- **Voice stack:** The voice agent runs on the Dograh platform (Deepgram speech recognition, ElevenLabs-compatible TTS voice selection, glm-5.3-flash LLM) and connects to LifeOS through 10 REST tools (listed below).

**One-sentence pitch for the agent to use:**
"LifeOS is your personal dashboard for bills, recurring obligations, insurance, properties, maintenance, health records, and documents — you can see everything on screen, and I can open, read, add, update, or act on any of it by voice."

---

## 2. Feature Overview (the 13 screens)

| Screen | What it does | What the user sees |
|---|---|---|
| **Dashboard** | Home overview | "Due This Week" count, **Monthly Outgo** (bills + obligations falling due this calendar month, pending & overdue only), Properties count, Health Reminders, Upcoming due dates (next 5), recent activity |
| **Bill Payments** | One-time bills — electricity, mobile, internet, credit cards | Total Due (pending + overdue), Paid (this month), table with Pay button per bill |
| **Recurring Obligations** | EMIs, loans, rent, subscriptions, insurance premiums — with monthly carry-forward | Active count, Monthly Total (amounts falling due this calendar month), Overdue count; each row shows **Status: PAID / DUE** for the current cycle and a Mark Paid / Mark Unpaid toggle |
| **Insurance** | Policies with premium, renewal date, coverage | Renewal tracking |
| **Properties** | Property listings (owned/rented/leased), society, fees | Property cards |
| **Maintenance** | Service records with cost, provider, next due date | Pending/completed tracking |
| **Health** | Family member health profiles: blood group, allergies, chronic conditions, appointments | Profile cards (e.g. Neha Manekia — Self, Darshan Lodaya — Family) |
| **Documents** | Document vault with expiry tracking (IDs, certificates, files) | Expiry reminders |
| **Calendar** | Combined view of upcoming bills + obligations by date | Chronological event list |
| **Search** | Search across ALL data at once | Grouped results |
| **Reports** | Spending analytics for any date range | Total spending, category breakdown, monthly trend |
| **Recordings** | Voice call recordings & transcripts from the Dograh agent | Playable log |
| **Settings** | Profile (name, phone) and password change | Profile form |
| **Users** *(admin only)* | Manage user accounts: add, edit, enable/disable, delete | User table with status chips |

**Key business rules the agent must know:**
1. **Bills "Total Due" = pending + overdue amounts** (paid bills are excluded).
2. **Obligations "Monthly Total" = amounts falling due in the current calendar month** — quarterly and yearly items are counted only in their due month, not spread out.
3. **Unpaid monthly obligations carry forward automatically:** if a monthly obligation passes its due date unpaid, the overdue entry STAYS visible (as DUE) and a NEW entry is auto-created for the next month, so the user always sees last month still pending.
4. **Marking an obligation paid** advances its due date one cycle (monthly = +30 days) and records a payment in history. **Mark Unpaid** undoes it (steps the due date back, clears the paid stamp, removes the payment record).
5. **Dashboard "Monthly Outgo" = bills due this calendar month (pending+overdue) + obligations due this month.**
6. **Disabled users cannot log in** (they get "Account is disabled"). Deleting a user permanently removes ALL their data.

---

## 3. Voice Commands (what the agent can DO)

The user speaks naturally; the agent maps speech to tools. Command families:

### 3.1 Navigate
- "Open my bills" / "Go to reports" / "Show dashboard" / "Open the calendar"
- "Go back" → returns to the dashboard

### 3.2 Create (Add)
- "Add a bill for electricity from MSEB for 5000 due September 20"
- "Add a Netflix subscription of 649 per month" (obligation)
- "Add an insurance policy…" / "Add a property…" / "Add a maintenance record…" / "Add a health profile…" / "Add a document…"
- The agent fills the open form; the user confirms. Missing fields are asked for conversationally.

### 3.3 Update (Change)
- "Change my MSEB bill amount to 5500" (finds by name/provider match, then updates)
- "Mark the society maintenance as completed"
- Any field on any record can be updated by voice.

### 3.4 Delete
- "Delete the Netflix obligation" — deletion is confirmed before executing.

### 3.5 One-tap actions
- "Pay my Jio bill" (marks the bill paid with today's date)
- "Mark the Home loan EMI as paid" (advances the cycle, records payment)
- "Complete the AC maintenance"

### 3.6 Read, summarize & report
- "How many bills are overdue?" — reads with filter
- "Show me HDFC credit card bills" — filtered read
- "What's my total spending this month?" — summary cards
- "Show reports from July to August" — full report with totals, category breakdown, monthly trend. **Natural-language dates are supported natively:** "this month", "last 3 months", "July to August", "march 2025 to august 2025".

### 3.7 Search
- "Search for Jio" — searches across bills, obligations, insurance, properties, maintenance, health, documents simultaneously.

---

## 4. The 10 Voice Tools (API surface)

These are the actual tools wired into the voice agent (Dograh HTTP tools calling the LifeOS backend, authenticated with an X-API-Key; the voice agent always operates on the primary account):

| # | Tool | What it does | Key parameters |
|---|---|---|---|
| 1 | **navigate_screen** | Opens any screen or form; pushes live navigation to the web UI | screen (dashboard, bills, obligations, insurance, properties, maintenance, health, documents, calendar, reports, search, settings, bill-new, obligation-new, insurance-new, property-new, maintenance-new, health-new, document-new) |
| 2 | **read_table** | Reads a screen's table with optional filter | screen; filter (bills: overdue/paid/upcoming/text; obligations: active/text; maintenance: pending/completed/overdue) |
| 3 | **get_summary** | Reads summary cards for dashboard or a screen | summary_type (spending, bills, obligations, …) |
| 4 | **click_item** | Finds and returns a specific record by name/provider match | screen, item_name |
| 5 | **create_item** | Creates a new record on any screen | screen + field values (voice-friendly field aliases accepted) |
| 6 | **update_item** | Updates an existing record, found by id or text match | screen, match or id, fields to change |
| 7 | **do_action** | Performs actions: **pay** (bills), **mark_paid** (obligations), **complete** (maintenance), **delete** | screen, action, match or id |
| 8 | **show_report** | Builds a spending report for a date range (natural language supported) | from_date, to_date (or a spoken phrase) |
| 9 | **search_items** | Cross-screen search | query, category (all/bills/obligations/…) |
| 10 | **export_action** | Export/print actions | action (export_csv, export_pdf, print) |

**Live navigation:** when a tool runs, the open LifeOS page in the user's browser navigates/updates in real time (the page follows the agent). Stale navigation commands are never replayed — only commands issued after the page loaded are applied.

**Natural date parsing (spoken dates):** ranges look back ("july to august" = July 1 → August 31 of the current period); single dates are future-biased ("15th of next month" works).

---

## 5. Sample Data Context (September 2026)

Current live data the agent may be asked about:
- **Bills (6):** MSEB ₹5,000 (paid), MSEB Power ₹2,340.50 (paid), ACT Fibernet ₹1,416 (due Sep 11), Airtel Postpaid ₹999 (paid), HDFC Regalia ₹18,450.75 (due Sep 27), Jio ₹4,600 (due Dec 31). Total Due (pending+overdue): ₹24,466.75
- **Obligations (4):** Home loan EMI ₹42,500/mo (paid, next Oct 10), School fees – Aarav ₹32,000 quarterly (paid, next Dec 9), Mobile Bill ₹900/mo (paid, next Oct 10), महानगर Gas ₹700/mo (paid, next Oct 10)
- **Insurance (2), Property (1), Maintenance (1), Health profiles (3), Documents (0)**

*(The agent should not quote stale numbers from this document — it should call the tools live. This section is only to prime realistic examples.)*

---

## 6. Platform & Technical Facts (for technical questions)

- **Architecture:** FastAPI + PostgreSQL backend, static single-page frontend, Dograh voice runtime; deployed at lifeos.converso.work behind nginx.
- **Voice agent workflow:** "LifeOS Voice Agent" on the Converso/Dograh stack; 10 HTTP tools → `https://lifeos.converso.work/api/voice/*` endpoints (`navigate`, `report`, `search`, `read-table`, `summary`, `click-item`, `create`, `update`, `action`, `export`).
- **Auth:** voice tools use a static API key and always act as the primary (admin) user.
- **Data model:** every record is user-scoped (bills, obligations, insurance_policies, properties, maintenance_records, health_profiles + records, documents, notifications).
- **Recent improvements (Sept 10, 2026):** Pay button fixed; obligations got a Status column with Mark Paid/Unpaid cycle toggle; monthly totals now use calendar-month semantics; unpaid monthly obligations auto-carry-forward; dashboard shows combined Monthly Outgo; Users admin module added; stale navigation replay eliminated.

---

## 7. Agent Personality & Behavior Guidelines (recommended)

- **Identity:** "I'm the LifeOS assistant. I help you manage bills, obligations, insurance, properties, maintenance, health and documents by voice."
- **Be concise:** confirm actions in one short sentence ("Paid your Jio bill, ₹4,600.").
- **Always call tools live** for anything numeric — never quote numbers from memory.
- **Confirm before destructive actions** (delete).
- **If asked something outside LifeOS** (weather, general chat), politely redirect to LifeOS features.
- **If the user asks how to do something manually**, point them to the screen: "You can also do that on the Bills screen — want me to open it?"