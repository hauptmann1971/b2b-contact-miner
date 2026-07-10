# Auth & multi-tenant model

> Aligned with `models/tenant.py`, `utils/web_security.py`, `routes/auth_routes.py`, `/admin/users`.

## Concepts

| Term | Meaning |
|------|---------|
| **Tenant** | Company / organization — isolated pool of keywords, contacts, pipeline data |
| **User** | Person with login (password and/or Telegram) belonging to one tenant |
| **Role** | `viewer`, `member`, `owner`, `super_admin` |

Data isolation is **per tenant**, not per user. All users in one tenant share the same contacts and keywords.

## Bootstrap (first `init_db()`)

From `.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=...
ADMIN_TELEGRAM_IDS=544528206
DEFAULT_TENANT_SLUG=company
DEFAULT_TENANT_NAME=Company
```

Creates default tenant + **owner** in `users` table. `.env` is used only at bootstrap; daily login reads `users.password_hash`.

## Login methods

| Method | Route | Notes |
|--------|-------|-------|
| Password | `/login` → `POST /auth/login` | Session cookie |
| Telegram widget | `/login` or `/admin` with `?id=&hash=…` | User must exist in `users.telegram_id` |
| HTTP Basic | Any protected route | Fallback for API/export |

## Roles

| Role | Access |
|------|--------|
| `viewer` | Read keywords, contacts, stats |
| `member` | + add/delete keywords |
| `owner` | + admin console, user management, password/theme |
| `super_admin` | Platform admin (reserved) |

## Protected routes

Public: `/health`, `/health/live`, `/health/ready`, `/login`.

Require login (`viewer+`): `/`, `/user`, `/keywords`, `/contacts`, `/api/stats`, …

Require `member+`: `POST /add_keyword`, bulk add, delete keyword.

Require `owner`: `/admin` actions, `/admin/users`, `/llm-data`, `/api-docs`.

## User management (UI)

**Admin → Users** (`/admin/users`): create user, change role, activate/deactivate, set password.

No self-registration. Owner creates colleagues manually.

## Database tables

- `tenants` — `id`, `slug`, `name`, `is_active`
- `users` — `tenant_id`, `username`, `password_hash`, `telegram_id`, `role`, `is_active`
- Business tables (`keywords`, `contacts`, `task_queue`, …) have `tenant_id`

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## Code map

| Module | Role |
|--------|------|
| `services/tenant_bootstrap.py` | Schema migration + default tenant |
| `services/auth_service.py` | Password / Telegram lookup |
| `services/user_admin_service.py` | Admin CRUD for users |
| `utils/tenant_context.py` | `scoped_query()`, request context |
| `utils/web_security.py` | Decorators, session, CSRF |
