# Archive (local only, not in git)

This folder holds **superseded or one-off** files moved out of the active tree.
It is listed in `.gitignore` — contents stay on disk for reference but are not committed.

## Layout

| Subfolder | Contents |
|-----------|----------|
| `doc/` | Historical documentation (old migrations, SonarQube, GigaChat, duplicate quickstarts) |
| `installs/` | Legacy Windows install batch scripts |
| `deploy-ops/` | One-off production repair/deploy scripts (multitenant fix, user inspect) |
| `scripts-dev/` | Ad-hoc dev smoke scripts superseded by `pytest tests/` and `checkers/` |

## Active docs

Use [doc/README.md](../doc/README.md) for the current documentation index.
