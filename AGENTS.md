# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a minimal workspace with no committed application files yet. Keep the root clean and add code under clear top-level directories as the project grows:

- `src/` for application code and retrieval / PDF processing modules
- `tests/` for automated tests
- `assets/` for small static assets
- `fixtures/` for sample PDFs used in tests
- `docs/` for design notes and architecture decisions

Prefer small, single-purpose modules. Name files by responsibility, such as `src/pdf_loader.py`, `src/rag_pipeline.ts`, or `tests/test_pdf_loader.py`.

## Build, Test, and Development Commands
No build system is configured yet. When tooling is added, expose it through one entry point and document it here. Prefer script-based commands over ad hoc shell steps.

- `npm install` or `pip install -r requirements.txt`: install dependencies
- `npm test` or `pytest`: run the test suite
- `npm run dev` or `python -m src.main`: start the local development entry point

If you add a new toolchain, also add the corresponding scripts to `package.json`, `Makefile`, or equivalent.

## Coding Style & Naming Conventions
Use 2 spaces for JavaScript / TypeScript / JSON and 4 spaces for Python. Prefer descriptive names, `camelCase` for JS / TS variables and functions, `PascalCase` for classes, and `snake_case` for Python modules and tests. Keep functions focused and avoid large mixed-responsibility files.

Run the formatter and linter chosen for the stack before opening a PR. Common defaults are `prettier` + `eslint` for JS / TS and `black` + `ruff` for Python.

## Testing Guidelines
Place tests in `tests/` and mirror the source layout where practical. Use names like `test_<module>.py` or `<feature>.test.ts`. Add at least one test for every bug fix and for each public-facing module. Prefer fixture-driven tests for PDF inputs so failures stay reproducible.

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so follow Conventional Commits by default: `feat: add chunking pipeline`, `fix: handle empty PDF pages`. Keep commits scoped to one change.

PRs should include:

- a short description of the change
- linked issue or task ID when available
- test evidence
- screenshots or sample output when UI or document rendering changes

## Security & Configuration Tips
Do not commit real documents, secrets, or API keys. Keep local settings in ignored env files such as `.env.local`, and provide sanitized examples in `.env.example`.
