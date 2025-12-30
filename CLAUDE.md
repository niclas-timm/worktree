# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack ticketing system with Django 6.0 backend and React 19 + Vite 7 frontend. Uses PostgreSQL for production, SQLite3 for development.

## Commands

### Backend (Django)

```bash
# Run development server
uv run manage.py runserver

# Database migrations
uv run manage.py makemigrations
uv run manage.py migrate

# Create new app (must create directory first)
mkdir -p apps/<appname>
uv run manage.py startapp <appname> apps/<appname>
# Then update apps/<appname>/apps.py: name = 'apps.<appname>'

# Create superuser
uv run manage.py createsuperuser

# Lint Python code
ruff check .
ruff check --fix .
```

### Frontend (React)

```bash
cd frontend

npm run dev      # Dev server on localhost:3000
npm run build    # Production build to dist/
npm run lint     # ESLint check
```

### Full Stack Development

Run both servers simultaneously:
- Terminal 1: `uv run manage.py runserver` (port 8000)
- Terminal 2: `cd frontend && npm run dev` (port 3000)

Access via http://localhost:3000 (Vite proxies /api and /admin to Django)

## Architecture

### Backend Structure

```
backend/
├── config/          # Django project settings, urls, wsgi/asgi
└── apps/            # Django applications
    ├── core/        # Shared utilities (email service)
    ├── users/       # Custom User model with email-based auth
    ├── companies/   # (placeholder)
    ├── projects/    # (placeholder)
    └── issues/      # (placeholder)
```

### Frontend Structure

```
frontend/src/
├── contexts/        # React context (AuthContext)
├── pages/           # Route page components
├── components/ui/   # Shadcn/ui components
├── services/        # API client (Axios with interceptors)
└── lib/             # Utilities
```

### Key Patterns

- **Authentication**: Email-based with 6-digit verification codes, token auth via dj-rest-auth
- **Email Service**: Centralized in `apps/core/email/service.py`, template-based (HTML + TXT)
- **Frontend Auth**: AuthContext manages state, automatic token injection via Axios interceptors
- **Routing**: ProtectedRoute/PublicRoute wrappers handle auth redirects
- **Django serves SPA**: Production build from `frontend/dist/` served via Django static files

### API Endpoints

All API routes prefixed with `/api/`:
- `/api/auth/login/`, `/api/auth/registration/`, `/api/auth/logout/`
- `/api/auth/verify-email/`, `/api/auth/resend-verification/`
- `/api/auth/password/reset/`, `/api/auth/password/reset/confirm/`
- `/api/health/`

### Configuration

- **Python**: pyproject.toml with UV, Ruff linting (select = ["E", "F", "I"])
- **Node**: .nvmrc specifies v22
- **Frontend paths**: `@/` alias maps to `./src/`
- **Shadcn**: new-york style, lucide icons, neutral base color
