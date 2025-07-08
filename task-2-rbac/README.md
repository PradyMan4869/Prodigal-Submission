 # Task 2: Role-Based Access Control (RBAC) System

This project implements a production-style, multi-tenant Role-Based Access Control (RBAC) system using FastAPI, PostgreSQL, and Docker. It provides a RESTful API for managing organizations, departments, users, resources, and permissions, including guest access via shareable links.

## Architecture Overview

The system is built on a containerized, service-oriented architecture orchestrated with Docker Compose.

- **FastAPI Application (`api` service):** A Python-based API server that handles all business logic, including authentication, authorization, and data manipulation.
- **PostgreSQL Database (`db` service):** A relational database that stores all entities and their relationships (users, organizations, departments, roles, resources, etc.).
- **No-Alembic Approach:** For simplicity and robustness in this demo environment, database schema migrations are handled directly by SQLAlchemy on application startup. The application logic includes a retry mechanism to wait for the database to be ready, preventing race conditions.

The core of the RBAC logic is implemented through a `DepartmentMembership` table, which links users to departments with specific roles (Admin, Manager, Contributor, Viewer). Permissions are checked hierarchically using FastAPI dependencies, ensuring that API endpoints are protected based on user roles.

## Environment Setup

### Prerequisites

- Docker
- Docker Compose

### Configuration

Create a `.env` file in the project root directory (`task-2-rbac/`) by copying the example below. This file stores sensitive configuration details and is ignored by Git.

```ini
# Database Configuration
DATABASE_URL=postgresql://user:password@db/rbacdb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=rbacdb

# JWT Security Configuration
# Generate a strong key using: openssl rand -hex 32
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## How to Run

1.  **Build and Start the Services:** From the `task-2-rbac/` directory, run the following command. This will build the API image and start both the API and database containers in the background.

    ```bash
    docker-compose up --build -d
    ```

2.  **Access the API:** The API will be available at `http://localhost:8000`.

3.  **Interactive Documentation:** Navigate to `http://localhost:8000/docs` in your browser to access the interactive Swagger UI. You can use this interface to test all API endpoints.

## How to Stop

To stop and remove all containers, networks, and volumes, run:

```bash
docker-compose down -v
```
