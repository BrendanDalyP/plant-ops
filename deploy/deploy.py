"""
deploy.py · Publish fabric/ to a Fabric workspace with fabric-cicd. Finished in Part 7.
PURPOSE  A full deployment: create or update every in-scope item in the target workspace from what is in Git,
         with parameter.yml's values for the environment, and remove in-scope items that are no longer in Git.
PSEUDOCODE
  workspace = FabricWorkspace(workspace_id from WORKSPACE_ID, environment from ENVIRONMENT,
              repository_directory fabric/, item types Notebook and Lakehouse,
              token_credential = the Azure CLI's sign-in)
  publish_all_items(workspace)
  unpublish_all_orphan_items(workspace)
"""
# TODO (Part 7): build the FabricWorkspace above, then publish and unpublish.
raise SystemExit("deploy.py is not written yet: Part 7")
