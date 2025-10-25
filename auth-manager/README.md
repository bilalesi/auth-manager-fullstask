# Auth Manager Service

FastAPI microservice for managing Keycloak OAuth tokens, including refresh tokens, offline tokens, and access token generation.

## Features

- **Token Vault**: Secure storage for encrypted refresh and offline tokens
- **Access Token Generation**: Generate fresh access tokens using stored refresh/offline tokens
- **Token Validation**: Validate access tokens via Keycloak introspection
- **Offline Token Management**: Request, store, and revoke long-lived offline tokens
- **AES-256-CBC Encryption**: All tokens encrypted at rest

## Authentication Flow Architecture

### Overview

The Auth Manager service provides two distinct token management strategies:

1. **Session-based tokens** (refresh tokens) - For short to medium-running jobs
2. **Offline tokens** - For long-running background jobs requiring extended access

### Use Case 1: Initial Login & Session Token Storage

When a user logs in through the frontend, NextAuth handles the authentication and the refresh token is stored in the vault.

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant NextAuth
    participant Keycloak
    participant AuthManager
    participant Database

    User->>WebApp: Login Request
    WebApp->>NextAuth: Initiate OAuth Flow
    NextAuth->>Keycloak: Authorization Request
    Keycloak->>User: Login Page
    User->>Keycloak: Credentials
    Keycloak->>NextAuth: Authorization Code
    NextAuth->>Keycloak: Exchange Code for Tokens
    Keycloak-->>NextAuth: Access Token + Refresh Token + ID Token
    Keycloak-->>WebApp: Redirect to home page

    Note over NextAuth: JWT Callback Triggered
    NextAuth->>AuthManager: POST /api/v1/refresh-token<br/>(store refresh token)
    AuthManager->>Database: Encrypt & Store Refresh Token
    Database-->>AuthManager: Persistent Token ID

```

### Use Case 2: Short/Medium Running Jobs (Refresh Token Flow)

For jobs like Jupyter notebooks that need fresh access tokens during an active session.

```mermaid
sequenceDiagram
    participant Service as Job Service<br/>(Jupyter/API)
    participant Frontend
    participant AuthManager
    participant Database
    participant Keycloak

    Note over Service: Access Token Expired

    Service->>AuthManager: POST /api/v1/refresh-token-id<br/>Authorization: Bearer {access_token}
    AuthManager->>AuthManager: Extract Session ID from Token
    AuthManager->>Database: Query Refresh Token by Session ID
    Database-->>AuthManager: Persistent Token ID
    AuthManager-->>Service: { persistentTokenId }

    Service->>AuthManager: GET /api/v1/access-token?id={persistentTokenId}<br/>Authorization: Bearer {access_token}
    AuthManager->>Database: Retrieve Encrypted Refresh Token
    Database-->>AuthManager: Encrypted Refresh Token
    AuthManager->>AuthManager: Decrypt Refresh Token
    AuthManager->>Keycloak: Get new access+refresh token
    Keycloak-->>AuthManager: New Access Token + Refresh Token
    AuthManager->>Database: Update Refresh Token
    AuthManager-->>Service: { accessToken, expiresIn }

    Note over Service: Continue with New Access Token
```

### Use Case 3: Long Running Jobs (Offline Token Flow)

For background jobs that need access beyond the user's active session.

#### Step 3a: Request Offline Token Consent

```mermaid
sequenceDiagram
    participant Service as Background Job
    participant Frontend
    participant AuthManager
    participant Database
    participant Keycloak
    participant User

    Service->>AuthManager: POST /api/v1/offline-token<br/>Authorization: Bearer {access_token}
    AuthManager->>AuthManager: Extract User ID & Session State
    AuthManager->>AuthManager: Generate State Token
    AuthManager->>AuthManager: Build Consent URL with offline_access scope
    AuthManager-->>Service: { consentUrl, stateToken, sessionStateId }

    Service->>Frontend: Return Consent URL
    Frontend->>User: Display "Grant Access" Button
    User->>Frontend: Click Grant Access
    Frontend->>Keycloak: Redirect to Consent URL
    Keycloak->>User: Show Consent Screen<br/>(offline_access scope)
    User->>Keycloak: Grant Consent

    Keycloak->>AuthManager: GET /api/v1/offline-token/callback<br/>?code={auth_code}&state={state_token}
    AuthManager->>AuthManager: Validate State Token
    AuthManager->>Keycloak: Exchange Code for Offline Token
    Keycloak-->>AuthManager: Offline Token + Access Token
    AuthManager->>Database: Encrypt & Store Offline Token<br/>(status: active)
    Database-->>AuthManager: Persistent Token ID
    AuthManager->>Frontend: Redirect to /consent-feedback<br/>?status=success
    Frontend-->>User: "Access Granted Successfully"
```

#### Step 3b: Use Offline Token for Access

```mermaid
sequenceDiagram
    participant Service as Background Job
    participant AuthManager
    participant Database
    participant Keycloak

    Note over Service: Need Access Token for Long Job

    Service->>AuthManager: POST /api/v1/offline-token-id<br/>Authorization: Bearer {access_token}
    AuthManager->>AuthManager: Extract Session ID from Token
    AuthManager->>Database: Query Offline Token by Session ID
    Database-->>AuthManager: Offline Token entry
    AuthManager->>Database: Create New Persistent Token ID<br/>(linked to same offline token)
    Database-->>AuthManager: New Persistent Token ID
    AuthManager-->>Service: { persistentTokenId }

    Service->>AuthManager: GET /api/v1/access-token?id={persistentTokenId}<br/>Authorization: Bearer {access_token}
    AuthManager->>Database: Retrieve Encrypted Offline Token
    Database-->>AuthManager: Encrypted Offline Token
    AuthManager->>AuthManager: Decrypt Offline Token
    AuthManager->>Keycloak: Refresh with Offline Token
    Keycloak-->>AuthManager: New Access Token
    AuthManager-->>Service: { accessToken, expiresIn }

    Note over Service: Use Access Token for Extended Period<br/>(Can repeat this flow as needed)
```

### Use Case 4: Token Validation

```mermaid
sequenceDiagram
    participant Service
    participant AuthManager
    participant Keycloak

    Service->>AuthManager: GET /api/v1/validate-token<br/>Authorization: Bearer {access_token}
    AuthManager->>Keycloak: Introspect Token
    Keycloak-->>AuthManager: Token Metadata<br/>(active, exp, user info)
    AuthManager-->>Service: { valid: True }
```

### Use Case 5: Revoke Offline Token

When a background job completes, it should clean up by revoking its offline token.

```mermaid
sequenceDiagram
    participant Service as Background Job
    participant AuthManager
    participant Database
    participant Keycloak

    Note over Service: Job Completed Successfully

    Service->>AuthManager: DELETE /api/v1/offline-token-id?id={persistentTokenId}<br/>Authorization: Bearer {access_token}
    AuthManager->>Database: Retrieve Offline Token
    Database-->>AuthManager: Offline Token entry
    AuthManager->>Database: Check if Token Shared<br/>(same session id)

    alt Token is Shared
        AuthManager->>Database: Delete Only This Persistent ID
        AuthManager-->>Service: { revoked: false, message: "ID removed" }
    else Token is Not Shared
        AuthManager->>Keycloak: Revoke Offline Token
        Keycloak-->>AuthManager: Success
        AuthManager-->>Service: { revoked: true, message: "Token revoked" }
    end

    Note over Service: Cleanup Complete
```

### Key Concepts

- **Persistent Token ID**: A uuid that references an encrypted token in the vault
- **Session State ID**: Keycloak session identifier used to link tokens to user sessions
- **Refresh Token**: Short-lived token (typically minutes to hours) for active sessions
- **Offline Token**: Long-lived token (days to months) for background jobs
- **Ack State Token**: Encrypted JWT used to validate OAuth callback requests

### Security Features

- All tokens encrypted at rest using AES-256-CBC
- Bearer token authentication required for all operations

## Technology Stack

- **FastAPI** 0.119.1 - Modern async web framework
- **Python** 3.12+ - Latest Python features
- **SQLAlchemy** 2.0 - Async ORM for PostgreSQL
- **Pydantic** v2 - Data validation and settings
- **UV** - Fast Python package manager
- **PostgreSQL** 18 - Token vault database
- **Keycloak** - OAuth2/OIDC provider

## Project Structure

```
auth-manager-svc/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Core utilities
│   ├── db/               # Database models and repositories
│   ├── middleware/       # Custom middleware
│   ├── models/           # Pydantic models
│   └── services/         # Business logic
├── alembic/              # Database migrations
├── tests/                # Test suite
├── pyproject.toml        # Project dependencies
└── .env.example          # Environment variables template
```

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 18
- Keycloak instance
- UV package manager

### Installation

1. Install UV (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository and navigate to the service directory:

```bash
cd auth-manager-svc
```

3. Create a virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install
make install-dev
```

### Configure Environment

4. Copy the environment template and configure:

```bash
make env
# Edit .env with your configuration
```

### Generate encryption key and ack state secret and update .env

```bash
export ENCRYPTION_KEY=$(openssl rand -hex 32)
echo "AUTH_MANAGER_TOKEN_VAULT_ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
```

```bash
export STATE_TOKEN_SECRET=$(openssl rand -base64 32)
echo "STATE_TOKEN_SECRET=$STATE_TOKEN_SECRET" >> .env
```

### Copy Keycloak client secret

```bash
1. select service realm
2. go to clients
3. select your service client (in dev env is : auth)
4. go to credentials
5. copy "Client Secret" to KEYCLOAK_CLIENT_SECRET
```

### Add redirect urls to whitelist

```bash
1. select service realm
2. go to clients
3. select your service client (in dev env is : auth)
4. add redirect url for consent to the list
5. add redirect url after consent (after granting consent) to the list
```

### Run database migrations:

```bash
make db-migrate
```

### Running the Service

Development mode with auto-reload:

```bash
make dev-local
```

## API Documentation

Once running, access the interactive API documentation:

- **Scalar UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `DATABASE_URL` - PostgreSQL connection string
- `KEYCLOAK_*` - Keycloak configuration
- `AUTH_MANAGER_TOKEN_VAULT_ENCRYPTION_KEY` - 64-char hex encryption key
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Development

#### Code Formatting

```bash
make format
```

#### Linting

```bash
make lint
```

#### Type checking

```bash
make type
```

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Start all services (PostgreSQL + Auth Manager)
make dev-docker

# Start with Keycloak for local development
make dev-local

# Stop services
make down
```

### Production Docker Build

```bash
# Build the image
make bake
```

```bash
# Deploy the image
make deploy
```

## Database Migrations

Migrations run automatically on container startup. For manual control:

```bash
# Run migrations
make db-migrate

# Create new migration
make db-revision MESSAGE="description"
```

## Health Checks

- **Liveness**: `GET /health` - Returns service status
- **Readiness**: `GET /health/ready` - Checks database connectivity
- **Version**: `GET /version` - Checks app tools versions

Copyright © 2025 Open Brain Institute
