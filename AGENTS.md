# Project guidance

These instructions apply to the entire repository.

## Project context

Wyoming–Halogen is an async Python proxy that exposes Halogen speech models to Wyoming clients. It requires Python 3.11 or newer. Read `README.md` and the relevant source before making changes.

## Changes and validation

- Keep changes focused and consistent with the existing code.
- Run relevant tests for behavior changes. Install test dependencies with `pip install '.[test]'` and run `pytest`.
- Report validation performed and any remaining limitations in the pull request.
- Never commit secrets or local environment files.

## Documentation

- Document all important project information in `/docs` at the repository root.
- This includes architecture, significant design decisions, configuration, protocol contracts, operational procedures, and important behavior changes.
- Create `/docs` when adding its first document. Use descriptive Markdown filenames and keep documentation current in the same PR as the related change.
- Keep `README.md` as the entry point for setup and usage, linking to detailed documentation in `/docs` where appropriate.

## Pull requests

Every PR must include these sections with meaningful content:

- **Description:** Summarize the change and its resulting behavior.
- **What and why:** Explain what changed, why it is needed, and any important design decisions.
- **Risks:** Describe potential regressions, compatibility or operational risks, and mitigations. Explicitly state when no known risks exist.

Include validation results and links to relevant `/docs` documentation when applicable. Use the repository pull request template.
