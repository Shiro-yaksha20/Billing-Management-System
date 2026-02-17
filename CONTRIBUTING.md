# Contributing to Salon Billing System

Thanks for your interest in contributing! This document explains how to get started.

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Billing-Management-System.git
   cd Billing-Management-System
   ```
3. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. **Run the tests** to make sure everything works:
   ```bash
   python -m pytest
   ```

---

## Development Workflow

1. Create a feature branch from `master`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your changes following the coding conventions below.
3. Run the full test suite:
   ```bash
   python -m pytest --cov=app --cov-report=term-missing
   ```
4. Commit using the [conventional commit](#commit-messages) format.
5. Push your branch and open a **Pull Request** against `master`.

---

## Coding Conventions

This project follows strict architecture and style rules documented in
[`.github/copilot-instructions.md`](.github/copilot-instructions.md). Key points:

### Architecture

```
UI (app/ui/)  ?  Services (app/services/)  ?  Repositories (app/repositories/)  ?  Infrastructure (app/infrastructure/)
```

- Dependencies flow **downward only**.
- UI never imports repositories or database sessions.
- Services never import PyQt6.
- All business logic lives in services.
- DTOs are `frozen=True` dataclasses in `app/dto/`.

### Style

- **Formatter:** `black` (line length 88)
- **Import sorter:** `isort` (profile: black)
- **Linter:** `flake8`
- **Type checker:** `mypy` (strict)
- **Python version:** 3.10+
- Use `Decimal` for monetary values, never `float`.
- Add `from __future__ import annotations` to every module.
- Add type hints to all public methods.
- Add docstrings to all public classes and methods.

### Naming

| Element | Convention | Example |
|---------|------------|---------|
| View class | `*View` | `BillingView` |
| Dialog class | `*Dialog` | `CustomerDialog` |
| Service class | `*Service` / `*Catalog` | `BillingService` |
| Repository class | `*Repository` | `BillRepository` |
| DTO class | `*Data` / `*Info` / `*Result` | `BillData` |
| Exception class | `*Error` | `ValidationError` |

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

**Scopes:** `billing`, `customer`, `staff`, `services`, `ui`, `infra`, `backup`

**Examples:**
```
feat(billing): add multi-currency support
fix(ui): correct discount field validation
test(services): add edge case tests for tax calculation
docs: update README with new architecture
```

---

## Testing

- **Unit tests** go in `tests/unit/` — use mocks, no real database.
- **Integration tests** go in `tests/integration/` — use the `temp_db` fixture.
- **Test naming:** `test_<method>_<scenario>_<expected>`
- **Coverage target:** 80% overall, 90% for services.

---

## Reporting Issues

- Use [GitHub Issues](https://github.com/Shiro-yaksha20/Billing-Management-System/issues).
- Include steps to reproduce, expected vs actual behavior, and your Python/OS version.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
