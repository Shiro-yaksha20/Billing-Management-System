# Billing Management System — Execution Plan (Aligned)
# Billing Management System — Execution Plan (Aligned)

> This file is the actionable execution checklist aligned with the master upgrade guide.
> Apply tasks in phase order. Do not skip mandatory rules.

---

## Rule Precedence

1. `.github/copilot-instructions.md` — coding and architecture guardrails.
2. `docs/NEXT_STEPS.md` — execution sequencing and delivery checklist.
3. Existing module-level patterns — only when they do not conflict with (1) and (2).

---

## Phase 1 — Critical Fixes (Start Here)

- [x] Fix `app/constants.py` to use absolute paths and `billing.db`.
- [x] Replace hardcoded `?` money symbols with configurable currency display.
- [x] Add `currency_symbol` default (`"\u20B9"`) in settings flow.
- [x] Add `app/ui/helpers.py` with shared `format_money`, `open_pdf`, `confirm_action`, `send_whatsapp_receipt`.
- [x] Replace duplicated WhatsApp send logic with shared helper.
- [x] Replace duplicated PDF open logic with shared helper.
- [x] Add `timeout=(5, 30)` to all `requests.*` calls in infrastructure.
- [x] Add confirmation dialogs for dangerous actions (save/send/restore/toggle).
- [x] Replace UI `self.layout` shadowing with `self._main_layout`.
- [x] Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.

## Phase 2 — Rebranding

- [x] Replace user-facing “Salon” labels with “Business” labels.
- [x] Migrate settings keys from `salon_*` to `business_*`.
- [x] Rename keyring app name `SalonBillingApp` -> `BillingApp`.
- [x] Rename token directory `.salon_billing` -> `.billing_app`.
- [x] Use dynamic main window title from `business_name`.
- [x] Update WhatsApp template language to business wording.

## Phase 3 — Navigation Overhaul

- [x] Convert page views from `QDialog` to `QWidget` (`billing`, `customer`, `history`, `export`, `settings`).
- [x] Rebuild `MainWindow` using sidebar + `QStackedWidget` pages.
- [x] Add `refresh()` on each page and trigger on navigation change.
- [x] Remove `dialog.exec()` navigation flow.

## Phase 4 — Theme and UX Polish

- [x] Add `app/ui/theme.py` and global stylesheet.
- [x] Apply theme in `main.py` after `QApplication` creation.
- [x] Ensure interactive widgets have meaningful `setObjectName()` values.
- [x] Add `QScrollArea` where content may overflow.
- [x] Add keyboard shortcuts in `main_window.py` and billing page.
- [x] Apply table stretch + alternating row style standards.
- [x] Redesign dashboard stat cards and recent bills table.

## Phase 5 — Architecture Fixes

- [x] Set `check_same_thread=False` in `app/infrastructure/database.py`.
- [x] Add indexes for hot columns in `app/models.py`.
- [x] Add rotating log handler in `app/infrastructure/logging.py`.
- [x] Extract shared bill DTO converter to `app/dto/converters.py`.
- [x] Add SQL `LIKE/ILIKE` wildcard escaping helpers in repositories.
- [x] Replace dashboard Python aggregation with repository SQL aggregation.
- [x] Align bill preview pipeline with actual receipt generation path.

## Phase 6 — Hardening

- [x] Narrow broad exception handlers where safe and practical.
- [x] Add numeric validators to relevant UI fields.
- [x] Add backup password strength checks.
- [x] Protect cloud tokens using secure storage.
- [x] Add configurable bill number prefix formatting.
- [x] Add phone normalization and validation.
- [x] Wrap CSV import in a transaction-safe operation.
- [x] Avoid import-time logger side effects.

## Phase 7 — Testing and Documentation

- [x] Run full test suite and fix regressions from refactors.
- [x] Add tests for helper utilities and new repository behaviors.
- [x] Add tests for wildcard escaping and dashboard aggregation.
- [x] Update `README.md` to generic branding and latest UX behavior.
- [x] Update `CHANGELOG.md` with completed phased items.

---

## Delivery Rules for Every Phase

- [x] Keep strict layer boundaries (`UI -> Services -> Repositories -> Infrastructure/Models`).
- [x] Use `Decimal` for money end-to-end.
- [x] Keep strict typing and docstring requirements.
- [x] Do not add silent exception handling.
- [x] Validate changes with tests before closing a phase.
