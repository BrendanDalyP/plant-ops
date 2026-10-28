---
description: How tests are written in this repo
applyTo: "tests/**"
---
- pytest with plain `assert`; one behavior per test, named `test_<what should be true>`.
- To make a batch that breaks a rule, copy a real one with `dataclasses.replace`. Never edit or add files in `data/`.
- Expected counts come from `docs/rules.md`. Never run the code to find out what to expect.
- API tests call the app through `TestClient(create_app())`.
