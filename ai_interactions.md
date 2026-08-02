# AI Interactions Log

This project's stretch feature is the **Test Harness / Evaluation Script**
(`src/evaluate.py`), not an agentic workflow or a design-pattern exercise, so the
SF8 (Agentic Workflow) and SF10 (Design Pattern) templates below do not apply.

My reflection on collaborating with an AI assistant on this project — including one
**helpful** suggestion and one **flawed/incorrect** suggestion — is documented in
[`model_card.md`](model_card.md), Section 10 ("Responsible AI Reflection").

Short version:

- **Helpful:** the AI proposed reusing the existing 0–4.5 score as a normalized 0–1
  confidence and wiring an abstain threshold into the main path, which made the reliability
  fix small, behavior-changing, and testable.
- **Flawed:** earlier AI-generated `validate_user_prefs` code called `logging.warning`
  without importing `logging` and left the function uncalled — it would have crashed with a
  `NameError`. Caught on review; fixed with a proper module logger and wired into `main.py`.
