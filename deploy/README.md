# deploy/

How `fabric/` reaches the Test workspace. Nothing here runs on your machine: the **Deploy to Test** workflow
(`.github/workflows/deploy.yml`) runs both scripts after a merge to `main`, signed in as the deployment app.

| File | What it does |
| --- | --- |
| `deploy.py` | Publishes `fabric/` to the workspace in `WORKSPACE_ID` with fabric-cicd, using `fabric/parameter.yml`'s values for `ENVIRONMENT` |
| `verify.py` | Reads the workspace back and fails if a notebook is bound to another workspace's lakehouse, or if a Dev ID survived |

Changes to this folder need a review from the people in `CODEOWNERS`.
