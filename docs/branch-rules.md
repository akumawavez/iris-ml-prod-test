# Branch rules

`develop` is the default branch. `ppe` and `prod` exist so later promotion has a place to land. They do not deploy anything today.

## Rules we follow

- Work happens on `feature/<short-name>` branches cut from `develop`.
- Changes reach `develop`, `ppe`, and `prod` only through a pull request.
- The first three learning pull requests merge only after you approve them in the pull request.
- After those three, merging can switch to auto-merge. That switch is its own change.
- Do not force-push `develop`, `ppe`, or `prod`.
- Do not commit secrets. Credentials belong in Azure DevOps secret variables or a local `.env` file, both ignored by git.

## What GitHub Free can enforce

Protected branches on a private repository require GitHub Pro, GitHub Team, or GitHub Enterprise. On GitHub Free they are available for public repositories. Official reference: [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

This repo stays private, and we do not buy Pro for this exercise. The rules above are the working agreement. If the account already has Pro, apply this protection to `develop`, `ppe`, and `prod`:

1. Repository **Settings** → **Branches** → **Add branch ruleset** (or classic branch protection).
2. Require a pull request before merging.
3. Block force pushes and branch deletion.
4. Do not add required status checks until the Azure DevOps pipeline from the third learning pull request exists.

## Branches

| Branch | Role now |
|---|---|
| `feature/*` | One change, opened as a pull request |
| `develop` | Integration branch. The only branch that will deploy, and only after a later cost approval |
| `ppe` | Reserved. Tests can run. Deploy stays off |
| `prod` | Reserved. Tests can run. Deploy stays off |
