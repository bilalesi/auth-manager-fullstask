# Auth Manager Full-Stack Application

An authentication and token management system with fastapi backend and next.js frontend, integrated with Keycloak for OAuth2/OIDC.

## Architecture

**Backend** (`auth-manager/`) - fastapi microservice for secure token vault and management

- encrypted token storage (aes-256-cbc)
- access token generation from stored tokens
- token validation and introspection
- offline token management for background tasks
- RESTful API with OpenAPI docs

**Frontend** (`frontend/`) - Next.js 15 application with NextAuth.js

- keycloak authentication integration
- built-in token vault implementation (similar to backend, not 100% feature-complete)
  > Please use auth-manager swagger(scalar) docs for full specifications implementation
- can use backend service OR standalone implementation
- task management demo with persistent tokens

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ and pnpm
- Python 3.12+ (optional, for local backend dev)

## Available Commands

```bash
# Start both applications
make full-stack

# Start auth manager only
make vault

# Start frontend only
make window

```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8081/auth/admin (admin/admin)
- **Test User**: vault.obi/vault

## Technology Stack

**Backend**

- FastAPI 0.119+ (Python 3.12+)
- SQLAlchemy 2.0 + PostgreSQL 18
- Alembic (migrations)
- Pydantic v2
- Keycloak integration

**Frontend**

- Next.js 15 (App Router)
- NextAuth.js 4.24
- TypeScript 5
- Drizzle ORM + PostgreSQL
- Tailwind CSS 4

**Infrastructure**

- Keycloak 26.4
- PostgreSQL 18
- Docker & Docker Compose

## Documentation

- **Backend Details**: [auth-manager/README.md](auth-manager/README.md)
- **Frontend Details**: [frontend/README.md](frontend/README.md)

## Frontend Integration Modes

The frontend can operate in two modes:

1. **Standalone** (not-fully featured) - Uses built-in token vault implementation
2. **Backend Service** - Communicates with backend API

To use backend service, set in `frontend/.env.local`:

```bash
AUTH_MANAGER_SERVICE=http://localhost:8000/v1
```

When you sign in to the frontend, it automatically stores your refresh token in the backend vault, allowing you to immediately test backend API endpoints using the docs.

---

Copyright © 2025 Open Brain Institute
