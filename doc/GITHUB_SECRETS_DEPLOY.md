# GitHub Secrets Deploy Setup

This project can deploy from GitHub Actions and build server `.env` from repository secrets.

## 1) Add repository secrets

In GitHub: `Settings -> Secrets and variables -> Actions -> New repository secret`

Add these required secrets:

- `SSH_HOST`
- `SSH_PORT` (example: `22`)
- `SSH_USER`
- `SSH_KEY` (private key content for SSH auth)
- `APP_DIR` (absolute path to project on server, example: `/opt/b2b-contact-miner`)

- `DATABASE_URL`
- `REDIS_URL`
- `SERP_API_PROVIDER`
- `SERPAPI_KEY`

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `USE_OPENAI` (`true` or `false`)
- `USE_DEEPSEEK` (`true` or `false`)
- `USE_YANDEXGPT` (`true` or `false`)
- `YANDEX_OAUTH_TOKEN`
- `YANDEX_FOLDER_ID`

- `LLM_DATA_API_TOKEN`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

## 2) Run deployment

- Open `Actions -> Deploy To Server`
- Click `Run workflow`
- Select `ref` (default `main`)

## 3) What workflow does

- Connects to server via SSH
- Updates git checkout in `APP_DIR`
- Rebuilds `.env` from GitHub Secrets
- Enables strict LLM preflight:
  - `AUTO_REFRESH_YANDEX_IAM_BEFORE_RUN=true`
  - `PERSIST_REFRESHED_YANDEX_IAM_TO_ENV=true`
  - `ENFORCE_LLM_READY=true`
  - `LLM_HEALTHCHECK_BEFORE_RUN=true`

## Notes

- Keep `.env` out of git.
- Rotate `YANDEX_OAUTH_TOKEN` in GitHub Secrets if access is compromised.
- If `APP_DIR` is not a git repo on server, initialize/clone it first.
