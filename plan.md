# plan.md — Business Radar AI (SaaS MVP)

## 1) Objectives
- Prove the fragile core end-to-end: **PostgreSQL in-container + AI structured outputs + PDF/Excel generation**.
- Build an MVP SaaS that ingests businesses from multiple sources, runs **dedup → enrichment → prediction → scoring**, and generates **daily intelligence reports** (in-app + exports; email optional).
- Ship a responsive dashboard with **RBAC**, audit logs, scheduler visibility, and India-first geo model (Mumbai/Thane/Navi Mumbai seed → scale).

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation; do not proceed until green)
**Goal:** One Python script runs cleanly end-to-end.

1. **Websearch quick playbook (30 min):**
   - Best practice: SQLAlchemy async + asyncpg with Postgres in containers
   - ReportLab vs WeasyPrint tradeoffs (pick one; default ReportLab)
   - emergentintegrations structured JSON patterns + retries

2. **PostgreSQL in container:**
   - Install/start postgres service; create DB/user; add `DATABASE_URL` (do not touch MONGO_URL).
   - Verify connection from Python using SQLAlchemy async engine.

3. **POC script `poc_core.py`:**
   - Create minimal schema (or run SQL DDL) for `businesses`, `predictions`, `lead_scores`.
   - Insert 1 sample Mumbai business; read back.
   - Call Emergent LLM (universal key) with **3 structured JSON outputs**:
     - `enrich_business` (fill missing fields + infer category)
     - `predict_needs` (predicted_need, probability, reasoning)
     - `score_lead` (0–100 + HOT/WARM/COLD + reasoning)
   - Persist prediction + score rows tied to business.

4. **Report generation outputs:**
   - Generate a tiny daily report (JSON + PDF via ReportLab) from DB rows.
   - Generate Excel export via openpyxl + CSV export.

5. **Exit criteria:**
   - Script prints: “DB OK / LLM OK / PDF OK / XLSX OK” and artifacts are readable.
   - If anything fails: iterate prompts/schema/service startup until stable.

**Phase 1 user stories (POC validation):**
1. As a developer, I can connect to PostgreSQL from Python and read/write a business row.
2. As a developer, I can enrich a business via LLM and get valid structured JSON.
3. As a developer, I can predict needs with probability + reasoning in structured JSON.
4. As a developer, I can score a lead and categorize HOT/WARM/COLD.
5. As a developer, I can generate a PDF and an Excel file from DB data.

---

### Phase 2 — V1 App Development (MVP core + UI; delay OAuth/email “real sending”)
**Goal:** Working app around the proven core; auth kept minimal to unblock testing (email/password first).

1. **Backend foundation (FastAPI + async SQLAlchemy + Alembic or idempotent DDL):**
   - Implement normalized tables exactly as specified (`businesses`, `predictions`, `lead_scores`, `daily_reports`, `users`, `settings`, `audit_logs`, `user_preferences`, `saved_searches`).
   - Add required indexes; ensure FK constraints; JSONB where specified.

2. **Core pipeline services:**
   - `IDiscoverySource` interface: `fetchBusinesses(), validate(), normalize(), deduplicate()`.
   - Connectors:
     - CSVUploadConnector (working)
     - ManualEntryConnector (working)
     - OpenCorporatesConnector (placeholder; empty if no key in Settings)
     - MCAConnector (placeholder; empty + log)
   - Pipeline: fetch→validate→normalize→dedup (name+pincode+(phone|email), fuzzy)→LLM enrich→predict→score→persist.

3. **Reports + exports (in-app first):**
   - `generate_daily_report(date, filters)` stores JSONB + PDF path/blob in `daily_reports`.
   - Exports for filtered businesses: CSV/XLSX/PDF.

4. **Scheduler:**
   - APScheduler on app startup: daily job to generate today’s report.
   - Endpoint `/api/scheduler/status` for last run/next run/outcome.

5. **Auth (MVP, test-friendly):**
   - Email/password + JWT, bcrypt, RBAC dependencies.
   - Seed Admin “Dhananjay” with **temp password printed to backend logs**, `force_password_reset=True`.
   - Force-reset flow endpoint + UI.

6. **Audit logs:**
   - Middleware/service writes `audit_logs` for all mutating endpoints; failures must not break the request.

7. **Frontend (React + shadcn/ui + Tailwind):**
   - Routes: Login, Force Reset, Dashboard, Businesses (filters/search/export), Business Detail (tabs), Manual Entry, CSV Upload, Discovery, Reports, Preferences, Admin Users/Settings/Audit/Scheduler.
   - Data-testid on interactive elements; mobile responsive.

8. **Conclude Phase 2:**
   - Run testing_agent_v3 E2E; fix blocker bugs.

**Phase 2 user stories (MVP):**
1. As an Admin, I can log in with temp password and I’m forced to reset it.
2. As an Analyst, I can upload a CSV, preview rows, commit, and see dedup results.
3. As an Analyst, I can manually add a business and run enrich/predict/score.
4. As a user, I can filter/search/sort/paginate businesses and open a detail view.
5. As a user, I can view today’s daily report in-app and download PDF/XLSX/CSV.

---

### Phase 3 — Add Integrations + Hardening (OAuth + email + saved searches)
**Goal:** Turn placeholders into configurable integrations; improve reliability for scale.

1. **Admin Settings UI/API (singleton settings):**
   - Store Google OAuth client id/secret + email provider settings; validate inputs.

2. **Google OAuth (customer-owned creds):**
   - Enable Google login button only when configured.
   - Store provider fields in `users`; keep email/password backup.

3. **Email module (must be optional):**
   - `EmailService` interface + SendGrid/SMTP providers (both configurable; no hardcode).
   - Scheduled send of daily/weekly reports to opted-in users; if not configured, log + skip.

4. **User preferences + saved searches:**
   - Default filters, delivery email, daily/weekly toggles.

5. **Scale readiness:**
   - Add keyset pagination option, query plan checks, index tuning.
   - Prepare partitioning notes for `businesses` by registration_date/state (no migration yet).

6. **Conclude Phase 3:**
   - Run testing_agent_v3 E2E; fix issues.

**Phase 3 user stories:**
1. As an Admin, I can configure Google OAuth and then log in via Google.
2. As an Admin, I can configure email provider settings without restarting the app.
3. As a user, I can enable daily emails and receive/download the report (or see “skipped” if not configured).
4. As a user, I can save a search filter and reuse it.
5. As an Admin, I can review audit logs for user and settings changes.

---

### Phase 4 — Discovery Expansion + Quality (optional next)
- OpenCorporates real API integration when key is provided; stronger normalization.
- MCA connector remains placeholder until captcha/login solution is approved.
- Add background jobs for batch enrichment/scoring; better retry/timeout handling.

## 3) Next Actions (immediate)
1. Implement Phase 1 `poc_core.py` and run until fully green.
2. Lock JSON schemas for LLM outputs (pydantic models + strict validation + retries).
3. Decide PDF engine (ReportLab default) and finalize report layout for MVP.
4. Once POC is green, generate DB migrations and start Phase 2 build.

## 4) Success Criteria
- **POC:** Single script successfully (a) writes/reads Postgres, (b) gets structured enrichment/prediction/scoring via Emergent LLM, (c) generates valid PDF + XLSX + CSV.
- **MVP:** Users can ingest businesses (CSV/manual), dedup/enrich/predict/score them, browse/filter/export, and generate/view daily reports; scheduler status visible; audit logs recorded.
- **Integrations:** OAuth and email are **configurable**, disabled gracefully when not set; no crashes; reports stored regardless of email status.
- **Performance:** Queries remain responsive with indexes; pagination works; schema ready for future partitioning.
