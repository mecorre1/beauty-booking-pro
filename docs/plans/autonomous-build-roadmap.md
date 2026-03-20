# Autonomous build roadmap (admin productivity first)

**Source of truth:** `docs/SPEC.md` and each `docs/user-stories/US-*.md`.  
**Already done:** US-001, US-002, US-003 (do not rebuild).

This document is the **executable contract** for finishing US-004–US-012 in order. Each story is one autonomous “run”: implement → test → mark **Done** in that story file → proceed.

---

## Global execution rules

1. **Before coding:** Open the target `docs/user-stories/US-XXX.md` and align every change with `docs/SPEC.md`. If the story and spec disagree, stop and fix the story or spec before implementing.
2. **Story status:** Set **In progress** only for the story you are building; clear it when moving on. On success, check **Done** and uncheck **To do** / **In progress** per `docs/templates/us-template.md`.
3. **Tests:** Add pytest for new/changed FastAPI behavior; add Vitest for new/changed Vue. Tests live next to the code (project convention).
4. **Verify locally after each story:**

   ```bash
   # Backend (from backend/, venv active)
   pytest

   # Frontend (from frontend/)
   npm run test -- --run
   ```

   Adjust flags if the repo’s `package.json` uses a different test script; the gate is “green tests for the story you touched.”

5. **Handoff note for US-004:** Implement **`Salon` in US-011** (model, seed row, admin + public GET). **US-004** adds **`Booking`** and snapshot fields; it must not duplicate a second `Salon` definition—extend the existing model.

---

## Build order (optimized for admin productivity early)

| Step | US     | Theme                         |
|------|--------|-------------------------------|
| 1    | US-007 | Admin authentication          |
| 2    | US-011 | Salon entity (admin + public) |
| 3    | US-010 | Weekly templates + apply week |
| 4    | US-012 | `PriceEntry` + price resolution |
| 5    | US-004 | Create booking + confirm flow |
| 6    | US-005 | Client edit via token         |
| 7    | US-006 | Client cancel via token       |
| 8    | US-008 | Admin bookings list           |
| 9    | US-009 | Admin calendar week           |

**Dependency rationale:** US-007 unlocks all admin APIs. US-011 and US-010 let the hairdresser configure the business without client booking. US-012 makes slot/service pricing consistent before US-004 snapshots money. US-004 unlocks US-005/006 and US-008. US-009 needs authenticated week data and existing slots/bookings.

---

## Step 1 — US-007 Admin email/password authentication

**Goal:** Protect admin routes; login from Vue stores token.

**Implement (checklist):**

- [ ] Backend: `backend/app/api/routers/admin_auth.py` — register if story requires bootstrap, login, password hashing, JWT or session (must match frontend).
- [ ] Wire `backend/app/api/deps.py` so existing admin routers require auth.
- [ ] Frontend: `AdminLoginView.vue` + `frontend/src/api/admin.ts` aligned with token shape and base URL.

**Gate:** All acceptance criteria in `docs/user-stories/US-007.md` satisfied; pytest + Vitest green.

**Then:** Mark US-007 **Done**.

---

## Step 2 — US-011 Manage salon entity (admin)

**Goal:** Single-salon MVP: admin updates salon; clients can read salon for copy.

**Implement (checklist):**

- [ ] ORM + migration (or init pattern used in repo): `Salon` with fields per `docs/SPEC.md`.
- [ ] Seed one default salon row for local/dev if nothing exists (document in README if new command).
- [ ] Admin: `GET` + `PUT` (or PATCH) one resource; auth required.
- [ ] Public: `GET /api/public/salon` for client-facing data.
- [ ] Vitest: admin salon form.

**Gate:** US-011 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-011 **Done**.

---

## Step 3 — US-010 Weekly schedule templates (CRUD + apply)

**Goal:** Templates + apply to ISO week → `Slot` rows; document re-apply and conflict policy.

**Implement (checklist):**

- [ ] Models: `WeeklyTemplate`, `TemplateSlot` per spec.
- [ ] Admin APIs: CRUD templates; **apply** to `YYYY-WW` → insert `Slot` rows (snapshot semantics).
- [ ] Document: re-apply behavior (reject vs replace) and behavior when bookings conflict (per story).
- [ ] Minimal slot mutation: at least admin delete slot or small PATCH as story allows.
- [ ] Vitest: template UI + apply action.

**Gate:** US-010 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-010 **Done**.

---

## Step 4 — US-012 Service pricing by datetime range

**Goal:** `PriceEntry` admin CRUD; resolve price at **slot datetime** (or alternative—**document** in story + code); refactor US-002 client display and US-004 snapshot path to use resolved price.

**Implement (checklist):**

- [ ] Model + admin APIs; reject overlapping intervals (document rule).
- [ ] Public or internal resolution helper used by public slots/services and booking creation.
- [ ] Remove or narrow `AT_HOME_DISPLAY_SURCHARGE_EUR` usage per story once DB/constants strategy is clear.
- [ ] Vitest: admin price list + create.

**Gate:** US-012 acceptance criteria; pytest + Vitest green; no regression on US-001/US-002 public contracts without updating tests.

**Then:** Mark US-012 **Done**.

---

## Step 5 — US-004 Confirm booking (contact + create booking)

**Goal:** `POST /api/public/bookings` with full validation, snapshots, slot flip, at-home buffer overlap, email abstraction.

**Implement (checklist):**

- [ ] `Booking` model + relationships; `edit_token` unique; enums per spec.
- [ ] Validate slot available, duration vs service, single booking per slot, buffer overlap for home.
- [ ] `EmailSender` protocol + no-op/dev implementation; pytest asserts send attempted with edit link placeholder.
- [ ] Confirm view + success UI with link path for edit/cancel (routes may be completed in US-005/006).

**Gate:** US-004 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-004 **Done**.

---

## Step 6 — US-005 Client edits booking via magic link

**Goal:** `GET`/`PUT` (or `PATCH`) by token; current slot free for overlap recompute; document `edit_token` stability.

**Implement (checklist):**

- [ ] Public endpoints per story; overlap rules excluding current booking.
- [ ] `status=edited` on success; snapshots refreshed as needed.
- [ ] Route `/book/edit/:token` reusing wizard pieces.

**Gate:** US-005 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-005 **Done**.

---

## Step 7 — US-006 Client cancels booking via magic link

**Goal:** Cancel endpoint; restore slot + buffer; document idempotency.

**Gate:** US-006 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-006 **Done**.

---

## Step 8 — US-008 Admin dashboard: bookings list

**Goal:** Authenticated list API; upcoming vs past in UI.

**Gate:** US-008 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-008 **Done**.

---

## Step 9 — US-009 Admin calendar: slots and bookings

**Goal:** Week view with auth; merge or aggregate API—document choice; align week navigation with `frontend/src/utils/isoWeek.ts`.

**Gate:** US-009 acceptance criteria; pytest + Vitest green.

**Then:** Mark US-009 **Done**.

---

## Autonomous runner loop (for agents or humans)

For each step **N** in the table above:

1. Set **In progress** on `docs/user-stories/US-XXX.md` for that US only.
2. Complete the **Implement** checklist; satisfy **SPEC.md** and the story’s acceptance criteria.
3. Run **Global execution rules** verify commands; fix until green.
4. Set **Done** on the story; clear **In progress**.
5. Commit (if using git) with message `feat: US-XXX short description` or fixup as appropriate.
6. Start the next step.

**Stop condition:** Steps 1–9 all **Done**; full `pytest` and `npm run test` pass on clean tree.

---

## Optional full regression (release-style)

```bash
cd backend && pytest
cd ../frontend && npm run test -- --run
```

Add lint/typecheck only if already part of the repo’s standard scripts.
