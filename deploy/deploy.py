"""
deploy.py · Publish fabric/ to a Fabric workspace with fabric-cicd
PURPOSE  A full deployment: every item of the types in scope is created or updated in the target workspace
         from what is in Git, with parameter.yml's values for the environment; items of those types that
         are no longer in Git are removed.
PSEUDOCODE
  workspace = FabricWorkspace(target id from WORKSPACE_ID, environment from ENVIRONMENT, fabric/ as the
              repository directory, Notebook and Lakehouse in scope, the Azure CLI's sign-in as credential)
  publish_all_items(workspace)            create or update, with parameter.yml applied
  unpublish_all_orphan_items(workspace)   remove notebooks the repo no longer has (lakehouses are kept:
                                          fabric-cicd never unpublishes a lakehouse unless a feature flag says so)
NOTE     In GitHub Actions, azure/login signs the Azure CLI in as the deployment app (OIDC, no secret).
"""
# os reads the variables the workflow sets; AzureCliCredential is the sign-in azure/login made
import os
from pathlib import Path

from azure.identity import AzureCliCredential
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

ROOT = Path(__file__).resolve().parents[1]                  # the repo root, wherever the script is run from

workspace = FabricWorkspace(
    workspace_id=os.environ["WORKSPACE_ID"],                 # the Test workspace (a GitHub environment variable)
    environment=os.environ.get("ENVIRONMENT", "TEST"),       # picks the TEST values in fabric/parameter.yml
    repository_directory=str(ROOT / "fabric"),              # the item folders Fabric wrote from Dev
    item_type_in_scope=["Notebook", "Lakehouse"],            # Ops_Model is left out: it needs its own parameters
    token_credential=AzureCliCredential(),                   # required: fabric-cicd has no default credential
)
publish_all_items(workspace)                                 # create or update every in-scope item
unpublish_all_orphan_items(workspace)                        # remove notebooks Git no longer has; lakehouses stay
