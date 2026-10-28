---
name: Deployment parameters
about: The parameter file fabric-cicd needs to deploy fabric/ to the Test workspace, sized for Copilot cloud agent
title: "Add fabric/parameter.yml for the TEST environment"
labels: []
---

## Outcome

When fabric-cicd deploys `fabric/` to the Test workspace (environment `TEST`), every Dev ID on the notebooks' `# META` lines is replaced: the default lakehouse and each `known_lakehouses` entry with `$items.Lakehouse.Ops_Lakehouse.$id`, and the default lakehouse's workspace with `$workspace.$id`.

## Acceptance tests

- [ ] `fabric/parameter.yml` uses `find_replace` entries with `is_regex: "true"`, `item_type: "Notebook"` and a `TEST` value; each regex captures only the ID.
- [ ] `tests/test_parameter_yml.py` applies each entry the way fabric-cicd does. Run with `-s`, it prints the `# META` line each entry matched. It fails if an entry matches no line, if an entry has no `TEST` value, or if any GUID from a `# META` line survives.
- [ ] `pytest -q` and `ruff check .` pass.

## Files to touch

- `fabric/parameter.yml`
- `tests/test_parameter_yml.py`

## How to verify

`pytest -q tests/test_parameter_yml.py -s`

## Out of scope

`deploy/`, `.github/`, anything inside the item folders under `fabric/`.
