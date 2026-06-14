# plan.md — Business Radar AI (SaaS MVP)

## 1) Objectives
- **Status update:** Phase 1 (POC) and Phase 2 (Full MVP) are **completed and validated**.
- Provide a production-grade MVP SaaS that:
  - Ingests newly registered businesses from multiple sources (pluggable connectors).
  - Runs a single unified pipeline: **validate → normalize → dedup → AI enrich → AI predict → AI score → persist**.
  - Delivers daily intelligence: **in-app dashboards + PDF/Excel/CSV exports**, with optional scheduled email delivery.
  - Enforces **JWT auth + RBAC** (Admin/Analyst/Subscriber) + **audit logs** for every mutation.
  - Is India-first with a scalable geo model (start Mumbai/Thane/Navi Mumbai → scale India-wide).
- Maintain a **CRED-inspired premium dark UI**: high-end B2B feel, data-dense but calm, mobile responsive.

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation; do not proceed until green) ✅ COMPLETED
**Goal:** One Python script runs cleanly end-to-end.

1. **PostgreSQL in container:**
   - Installed PostgreSQL 15 and configured it.
   - Added DB/user and connection variables (without touching `MONGO_URL`).

2. **POC script `poc_core.py`:**
   - Verified async SQLAlchemy + asyncpg read/write.
   - Verified Emergent LLM structured JSON outputs for:
     - enrichment
     - predicted need
     - lead scoring

3. **Report outputs:**
   - Generated PDF (ReportLab), Excel (openpyxl), CSV.

**Exit criteria:**
- Script executed in a single run with all stages green.

**Artifacts:**
- `/app/backend/poc_core.py`

---

### Phase 2 — V1 App Development (MVP core + UI) ✅ COMPLETED
**Goal:** Working app around the proven core; RBAC + reports + exports + scheduler + audit.

#### 2.1 Backend (FastAPI + async SQLAlchemy + asyncpg + PostgreSQL)
**Implemented:**
1. **Database (normalized + indexed; analytics-ready):**
   - Tables: `users`, `businesses`, `predictions`, `lead_scores`, `daily_reports`, `settings`, `audit_logs`, `user_preferences`, `saved_searches`, `scheduler_runs`.
   - Indexes on: `business_name`, `city`, `state`, `registration_date`, `pincode`, `lead_scores.score`, `predictions.predicted_need`, plus FK indexes.
   - JSONB used for flexible payloads (`businesses.extra`, `daily_reports.report_json`, etc.).

2. **Auth + Security:**
   - Email/password login (bcrypt + JWT via PyJWT).
   - Force-password-reset flow.
   - RBAC enforced across routes (Admin/Analyst/Subscriber).
   - Google OAuth bootstrap endpoints:
     - `/api/auth/google/status`
     - `/api/auth/google/start`
     (UI disables until configured in Settings; not hardcoded).

3. **Discovery architecture (pluggable connectors):**
   - `IDiscoverySource` interface semantics implemented.
   - Connectors:
     - `manual` (manual entry)
     - `csv_upload` (CSV ingestion)
     - `opencorporates` (**placeholder fetch**, token-aware)
     - `mca` (**placeholder**)
     - `sample_seed` (working; realistic Mumbai/Thane/Navi Mumbai synthetic discovery)

4. **Unified pipeline:**
   - Fuzzy dedup using RapidFuzz on normalized name + pincode + phone/email.
   - AI pipeline via Emergent universal LLM key:
     - enrichment (category, subcategory, company_type, employee_estimate, confidence_score)
     - need prediction (predicted_need, probability, reasoning)
     - lead scoring (score 0–100, HOT/WARM/COLD, scoring_reason)

5. **Reports + exports:**
   - Daily report generation: JSON + PDF (ReportLab) persisted.
   - Exports:
     - Businesses: CSV + XLSX (API endpoints)
     - Reports: PDF + CSV + XLSX

6. **Scheduler (APScheduler):**
   - Daily report job scheduled at **08:00 IST** (configurable via Settings).
   - Admin endpoints for:
     - status (last runs + next run)
     - run-now
   - Scheduler run history stored in `scheduler_runs`.

7. **Email module (optional; system works without it):**
   - `EmailService` design via pluggable providers:
     - SendGrid provider (API-based)
     - SMTP provider
   - Provider credentials stored in Settings.
   - If not configured: delivery is silently skipped; reports still generated and stored.

8. **Audit logs:**
   - Every mutating action writes to `audit_logs` (non-fatal if logging fails).

9. **Seeding (idempotent):**
   - Creates:
     - Primary admin: `dhananjay@businessradar.ai` (force_password_reset=true; temp password printed to logs)
     - QA users:
       - `test.admin@businessradar.ai / RadarTest@2025`
       - `test.analyst@businessradar.ai / AnalystTest@2025`
       - `test.subscriber@businessradar.ai / SubTest@2025`
   - Inserts ~15 sample businesses using `sample_seed` connector with AI enrichment.

10. **PostgreSQL resilience:**
   - PostgreSQL is managed via supervisor (`program:postgresql`).

#### 2.2 Frontend (React 19 + shadcn/ui + Tailwind + Recharts + framer-motion)
**Implemented:**
1. **CRED-inspired premium dark theme:**
   - Near-black canvas, gold accents, glassy surfaces, eyebrow labels, refined motion.
   - HOT/WARM/COLD status pills.

2. **Routes (all delivered):**
- `/login`
- `/force-reset`
- `/dashboard`
- `/businesses`
- `/businesses/:id`
- `/businesses/new`
- `/businesses/upload`
- `/discovery`
- `/reports`
- `/reports/:id`
- `/preferences`
- `/admin/users`
- `/admin/settings`
- `/admin/audit-logs`
- `/admin/scheduler`

3. **RBAC UI enforcement:**
   - Subscriber sees read-only nav and actions.
   - Analyst/Admin see mutation actions.

4. **Mobile responsiveness:**
   - Sidebar via sheet drawer.
   - Filter rail becomes mobile sheet.

5. **Testing readiness:**
   - `data-testid` coverage across interactive elements.

---

### Phase 3 — Add Integrations + Hardening (OAuth + email + real discovery) 🔜 NEXT
**Goal:** Convert placeholders into real integrations; production hardening for scale.

1. **Google OAuth completion:**
   - Implement callback endpoint + token exchange + user provisioning.
   - Support multiple OAuth providers in future.

2. **Email delivery completion:**
   - Attach PDF report and/or provide secure download links.
   - Add delivery logs table (sent/skipped/failure reasons).

3. **Real OpenCorporates integration:**
   - Implement actual API calls (requires user-provided token).
   - Improve normalization + pagination/ratelimiting.

4. **MCA connector strategy:**
   - Keep placeholder unless captcha/login solution is approved.
   - Optionally add “manual MCA CSV export import” workflow as an interim solution.

5. **Scale hardening:**
   - Alembic migrations.
   - Query plan checks + index tuning.
   - Partitioning strategy for `businesses` by `registration_date`/`state`.
   - Observability (structured logs, metrics) and rate limiting.

6. **Security hardening:**
   - Remove/rotate seeded QA accounts in production.
   - Optional MFA/2FA.

**Phase 3 user stories:**
1. As an Admin, I can configure Google OAuth and complete Google sign-in.
2. As an Admin, I can configure email delivery and see delivery logs.
3. As an Analyst, I can run real OpenCorporates discovery and ingest results.
4. As an Admin, I can manage scale features (migrations, scheduling, partition notes).

---

### Phase 4 — Discovery Expansion + Quality (optional next)
- WhatsApp/Telegram delivery.
- API-based report delivery for Enterprise/Reseller/API Partner.
- Bulk/background enrichment and scoring with retry queues.
- Advanced dedup entity resolution across states.
- Saved searches UI enhancements + alerts.

## 3) Next Actions (immediate)
1. **Decide integration scope for next iteration:**
   - Provide OpenCorporates API token to enable real discovery.
   - Provide SendGrid key (optional) and confirm sender domain.
   - Provide Google OAuth Client ID/Secret + Redirect URI.
2. **Production readiness checklist:**
   - Remove/rotate QA users.
   - Configure JWT secret + DB credentials securely.
   - Enable HTTPS-only cookie storage if moving to cookie-based auth.
3. **Hardening improvements:**
   - Add Alembic migrations.
   - Add delivery logs table.
   - Add keyset pagination for large datasets.

## 4) Success Criteria
- **POC:** ✅ Completed — Postgres + structured AI JSON + PDF/XLSX/CSV green in a single run.
- **MVP:** ✅ Completed — ingestion (manual/CSV/discovery), dedup/enrich/predict/score, browse/filter, in-app reports + exports, scheduler status, audit logs.
- **Integrations:** UI and backend are **configurable and safe-by-default**:
  - Google OAuth is present but disabled until configured.
  - Email delivery never blocks report generation.
  - Discovery connectors support placeholders and future real integrations.
- **Quality:** ✅ E2E validated (testing_agent_v3): backend 41/41 pass; frontend issues fixed (Subscriber “Add” button hidden).
- **Scale readiness:** normalized schema + indexes present; migration + partitioning + observability planned for Phase 3.
