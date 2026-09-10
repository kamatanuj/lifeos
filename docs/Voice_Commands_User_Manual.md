# LifeOS Voice Assistant — User Manual

**LifeOS** (lifeos.converso.work) — Voice commands for Add, Update & Delete
*Voice engine: Converso (converso.work) / Dograh — your voice assistant lives inside the LifeOS web app.*

---

## 1. Getting Started — How to Start Talking

1. Open **https://lifeos.converso.work** in Chrome (a mic is required).
2. Log in as usual.
3. Click the **green "L" button** at the bottom-right corner of the screen — this starts the LifeOS voice agent (powered by Converso at converso.work).
   - On Dograh Cloud deployments, use the green **"Talk to Agent"** button instead.
   - Tip: add **`?voice=local`** to the URL (e.g. `https://lifeos.converso.work/?voice=local`) and the voice session starts automatically after you log in.
4. Allow microphone access when the browser asks (first time only).
5. The assistant greets you: *"Hi! I'm your LifeOS assistant."*
6. Speak naturally. The assistant confirms every action in **one short sentence**, and the screen behind it updates live.

**To end the session:** click the mic/stop button in the voice widget.

> You can also control LifeOS by plain typing (text chat) — every command in this manual works the same way.

---

## 2. The Golden Rule of Adding Data

You don't need to say every field. Speak naturally — the assistant:

- **Fills in what you said** (provider, amount, dates…).
- **Auto-derives what you didn't say** (e.g. "MSEB" → it knows it's an *electricity* bill; "my Powai flat" → it knows it's an *apartment*).
- **Asks you conversationally for anything still missing**: *"I can add the bill — I just need a bit more info: due date. Please tell me the due date and I'll create it."*

Dates are understood in natural speech: **"tomorrow", "next Tuesday", "25th August", "15th of next month", "in 3 days"** are all valid.

Amounts are flexible: say **"for 5000"**, **"for ₹5,000"** — both work.

---

## 3. ADD Commands (Create)

### 3.1 Bills — "Add a bill…"
*Required eventually: type, provider, amount, due date. The type is auto-guessed from the provider name (MSEB/Tata Power → electricity, Airtel/Jio → mobile, HDFC/ICICI → credit card, ACT/Hathway → internet, Indane → gas).*

| You say | What happens |
|---|---|
| **"Add a bill for electricity from MSEB for 5000, due on 20th September"** | Bill created instantly. "Created new bill: electricity bill from MSEB for ₹5,000 due 2026-09-20." |
| **"Add my Airtel mobile bill of 599 due tomorrow"** | Type auto-set to *mobile*, provider Airtel, amount 599. |
| **"Add a credit card bill from HDFC for 8,500 due 5th of next month"** | Type auto-set to *credit_card*. |
| **"Add an electricity bill"** | Agent asks for the missing pieces: *"I just need a bit more info: provider, amount, due date."* Answer each in turn — it creates the bill once all are known. |
| **"Add a Jio bill for 399 due tomorrow, pay by UPI"** | Payment method recorded (upi_gpay, credit_card, net_banking, auto_pay, cash all accepted). |

### 3.2 Obligations (EMIs, loans, rent, subscriptions) — "Add an obligation…"
*Required eventually: name, category, amount, next due date. Category is auto-guessed from the name ("home loan" → loan, "rent" → rent, "Netflix" → subscription).*

| You say | What happens |
|---|---|
| **"Add Netflix subscription for 649 per month"** | Created: category *subscription*, frequency *monthly*. |
| **"Add my home loan EMI of 24,500 due on 5th of every month"** | Category auto-set to *loan*. |
| **"Add an obligation for rent, 22,000 monthly, next due 1st of next month"** | Category auto-set to *rent*. |
| **"Add a subscription for Spotify, 119 per month"** | Created without follow-up questions. |
| **"Add an obligation"** | Agent asks only for what's missing: name, category, amount, next due date. |

### 3.3 Insurance — "Add an insurance policy…"
*Required eventually: policy type, provider, premium, renewal date. Types: health, life, car, home, travel, pet.*

| You say | What happens |
|---|---|
| **"Add a health insurance policy from HDFC Ergo, premium 22,000, renewal on 15th March"** | Created: status auto-set to *active*. |
| **"Add my car insurance, Bajaj Allianz, premium 14,000, renews 1st October, coverage 8 lakhs"** | Coverage amount recorded. |
| **"Add a life policy from LIC, premium 48,000, renewal date 12th of next month, policy number 8839-2210"** | Policy number recorded. |
| **"Add an insurance policy"** | Agent asks for: policy type, provider, premium, renewal date. |

### 3.4 Properties — "Add a property…"
*Required eventually: name. That's it — the type is guessed from what you call it ("flat/apartment" → apartment, "house/villa/bungalow" → house, "plot/land" → plot, "shop/office" → commercial, "car/bike" → vehicle), and ownership defaults to *owned*.*

| You say | What happens |
|---|---|
| **"Add my Powai flat"** | Created: type auto-set to *apartment*, ownership *owned*. |
| **"Add a property called Green Villa in Lonavala"** | Type auto-set to *house*. |
| **"Add my shop in Andheri, rented, society name Sunrise Heights, society fee 3,000"** | Type *commercial*, ownership *rented*. |
| **"Add a plot in Whitefield, purchased March 2021, 40 lakhs"** | Type *plot*; purchase details recorded. |

### 3.5 Maintenance — "Add a maintenance record…"
*Required: just the title. The category is auto-derived from the title (AC → ac_service, tap/pipe → plumbing, wiring → electrical, cleaning, painting, pest control, water tank, gardening — anything else → general).*

| You say | What happens |
|---|---|
| **"Add maintenance record: AC service by CoolTech for 2,500, due on 28th September"** | Created: type auto-set to *ac_service*. |
| **"Log a maintenance record — kitchen tap repair, plumber Rajesh, 450"** | Type *plumbing*. |
| **"Add deep cleaning of the house next Tuesday"** | Type *cleaning*; date from "next Tuesday". |
| **"Add maintenance record for pest control, 1,800"** | Type *pest_control*. |

### 3.6 Health Profiles — "Add a health profile…"
*Required eventually: member name and relationship (self, spouse, child, parent, dependent).*

| You say | What happens |
|---|---|
| **"Add a health profile for myself"** | Agent confirms relationship as *self* and creates it. |
| **"Add health profile for my wife, blood group O+, allergic to peanuts"** | Created with blood group and allergies. |
| **"Add a health profile for my father, diabetic"** | Chronic condition recorded. |
| **"Add a health profile"** | Agent asks for member name and relationship. |

### 3.7 Documents — "Add a document…"
*Required eventually: name and category (e.g. passport, PAN card, insurance, agreement).*

| You say | What happens |
|---|---|
| **"Add a document — my passport, category travel, expiring 12th December 2030"** | Created with expiry tracked. |
| **"Add Aadhaar card to documents, category identity"** | Created. |
| **"Add a rental agreement document, category legal, expires in 11 months"** | Created with expiry date. |

---

## 4. UPDATE Commands (Change Existing Data)

Find the record by **name** (or part of a name) and say what to change. You never need ID numbers.

| You say | What happens |
|---|---|
| **"Change my MSEB bill amount to 5,500"** | Bill updated. *"Successfully updated the bill: electricity bill from MSEB for ₹5,500…"* |
| **"Update the Airtel bill due date to next Friday"** | Due date changed. |
| **"Change my Netflix subscription to 749 per month"** | Obligation amount updated. |
| **"Update HDFC Ergo renewal date to 20th March"** | Insurance renewal moved. |
| **"Update my Powai flat address to Lodha Aristo, Powai"** | Property address changed. |
| **"Change AC service cost to 2,800"** | Maintenance cost updated. |
| **"Mark the society maintenance as completed"** | Maintenance marked done (completion date = today). |
| **"Mark my MSEB bill as paid"** | Bill marked paid (paid today). |
| **"Mark the HDFC policy as lapsed"** | Insurance status → lapsed. |
| **"Mark the HDFC policy as renewed"** | Insurance status → active. |
| **"Mark the Jio bill as unpaid"** | Bill status → pending again. |

**How matching works:** the assistant looks for your words inside every field of that screen's records — so "MSEB", "the electricity one", or "Netflix" all work. If nothing matches, it says so: *"No bill found matching 'Vodafone'"* — try another name.

---

## 5. DELETE Commands

Deletion is one sentence and takes effect immediately — the record is removed and the screen refreshes.

| You say | What happens |
|---|---|
| **"Delete the Netflix obligation"** | *"Successfully deleted obligation: Netflix."* |
| **"Delete my MSEB bill"** | Bill removed from the bills table. |
| **"Delete the AC maintenance record"** | Maintenance record removed. |
| **"Delete the Powai flat from my properties"** | Property removed. |
| **"Delete the HDFC insurance policy"** | Policy removed. |
| **"Delete my health profile for my wife"** | Health profile removed. |
| **"Delete the rental agreement document"** | Document removed. |

> ⚠️ Deletions are permanent. The assistant confirms in one sentence — it does not ask twice. Say exactly what you want deleted.

---

## 6. ACTION Commands (One-tap operations)

| You say | What happens |
|---|---|
| **"Pay my Jio bill"** | Bill marked paid with today's date and full amount. |
| **"Pay the HDFC credit card bill"** | Same — instant pay. |
| **"Mark the Netflix obligation as paid"** | Last-paid date set to today. |
| **"Complete the AC maintenance"** | Marked completed as of today. |
| **"Go back"** | Returns to the dashboard. |

---

## 7. VIEW, SEARCH & REPORTS Commands (Read-only)

### 7.1 Navigate & read
| You say | What happens |
|---|---|
| **"Show me my bills"** / **"Go to insurance"** / **"Open dashboard"** | Navigates to that screen and reads out the summary. |
| **"Show my properties"**, **"Show health"**, **"Show documents"** | Same — any screen: bills, obligations, insurance, properties, maintenance, health, documents. |
| **"How many bills are overdue?"** | *"You have 1 overdue bill: BEST Electricity for ₹3,200."* |
| **"Show my paid bills"** / **"Show upcoming bills"** | Filtered table. |
| **"Show me HDFC credit card"** | Finds and reads that bill. |
| **"Show pending maintenance"** / **"Show active obligations"** | Filtered tables. |

### 7.2 Summaries
| You say | What happens |
|---|---|
| **"What's my total spending?"** | This month vs last month with % change. |
| **"What's my bills summary?"** | Pending / overdue / due-this-week counts. |
| **"How's my insurance?"** | Active policies, total premium & coverage. |

### 7.3 Search (across everything)
| You say | What happens |
|---|---|
| **"Search for HDFC"** | Finds HDFC in bills, insurance, documents… all at once. |
| **"Search for AC"** | Finds AC bills, AC maintenance, etc. |

### 7.4 Reports (date ranges in plain English)
| You say | What happens |
|---|---|
| **"Show reports from July to August"** | Report for 1 Jul – 31 Aug (whole months). |
| **"Report for July"** | Whole month of July, current year. |
| **"Show report for this month"** / **"last month"** | Month-based report. |
| **"Report for the last 3 months"** | Rolling 3-month report (includes current month). |
| **"Show reports for this year"** / **"last year"** | Year-based report. |
| **"July 2025 to August 2025"** | Whole months of that year. |

The report includes total spending, category breakdown, and monthly trend — read out and shown on the Reports screen.

---

## 8. Spoken Dates Cheat-Sheet

**For due dates / renewal dates / appointments** (future-looking):
- "tomorrow", "day after tomorrow", "in 3 days"
- "next Tuesday", "next Friday"
- "25th August", "August 25"
- "15th of next month", "next month"
- "end of the month"

**For reports** (range-looking):
- "july to august", "july 2025 to august 2025", "march to may"
- "this month", "last month", "next month"
- "last 3 months", "past 6 months"
- "this year", "last year"
- a single date like "15th august" (that day only)

---

## 9. What the Assistant Fills In For You (Auto-derivations)

| Screen | You omit | It auto-fills |
|---|---|---|
| Bills | bill type | Guessed from provider (MSEB→electricity, Airtel→mobile, HDFC→credit_card, ACT→internet, Indane→gas) |
| Obligations | category | Guessed from name (loan/EMI→loan, rent→rent, Netflix/Spotify→subscription, else other) |
| Properties | property type | Guessed from the name (flat→apartment, house→house, plot→plot, shop→commercial, car→vehicle) |
| Properties | ownership | Defaults to *owned* |
| Maintenance | type | Guessed from title (AC→ac_service, tap→plumbing, wiring→electrical, cleaning→cleaning, paint→painting, pest→pest_control, tank→water_tank, garden→gardening) |
| Insurance | status | Defaults to *active* |
| Bills | status | Defaults to *pending* |

If something still can't be derived and is required, the assistant asks for **only** the missing field(s) — conversationally, one short question at a time.

---

## 10. The Full Screen Map (what you can navigate by voice)

**Main screens:** Dashboard · Calendar · Search · Bills · Obligations · Insurance · Properties · Maintenance · Health · Documents · Reports · Settings

**Form screens** (opened with "Add a new…"): bill-new · obligation-new · insurance-new · property-new · maintenance-new · health-new · document-new

**One-sentence rule:** the assistant always confirms what it did in a single short sentence, e.g. *"Created new bill: electricity bill from MSEB for ₹5,000 due 2026-09-20."*

---

## 11. Tips & Troubleshooting

1. **Be specific about amounts and dates** in one breath when you can: *"Add an MSEB electricity bill for 5,000 due on 20th September"* → created instantly, no follow-ups.
2. **If the assistant asks for a missing field**, just answer it directly: *"5000"* or *"due next Friday"*.
3. **Matching is by keyword** — if "delete the bill" is ambiguous, say **"delete the MSEB bill"**.
4. **₹, commas, and "lakhs"** in amounts are all understood (₹5,000 / 5 lakhs).
5. **The screen updates live** while you speak — tables refresh after every add/update/delete; you'll see the change behind the voice bubble.
6. **"Go back"** always returns to the Dashboard.
7. **Export by voice:** say **"export report"** — CSV/PDF export of your bills is prepared for download.

---

*Manual generated 10 Sep 2026 · LifeOS voice agent (Converso/Dograh) · 10 voice tools: navigate_screen, create_item, update_item, do_action, read_table, click_item, get_summary, search_items, show_report, export_action*