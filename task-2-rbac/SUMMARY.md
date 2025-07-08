 
# Task 2 Summary: RBAC System

This document outlines the challenges faced, architectural decisions made, and potential improvements for the RBAC system implementation.

## Challenges Faced

1.  **Database Migrations with Docker:** The most significant challenge was setting up a reliable database migration workflow with Alembic inside a Dockerized environment. We encountered a series of cascading errors:
    - `ModuleNotFoundError`: Python path issues when running Alembic from the container's root.
    - `Template rendering failed`: Caused by Alembic's `autogenerate` feature struggling to handle custom Python `Enum` types.
    - `KeyError: 'None'` and `KeyError: 'base'`: Complex dependency and mapping errors related to initializing the first migration in a clean environment.

2.  **Startup Race Condition:** A classic Docker Compose problem where the API container would start and try to connect to the database before the PostgreSQL server was fully initialized and ready to accept connections, causing `OperationalError`.

## Architectural Decisions

1.  **Abandoning Alembic for Simplicity:** After multiple failed attempts to stabilize Alembic in this specific Docker environment, a strategic decision was made to remove it entirely. For a task of this scope, the complexity and debugging overhead of Alembic outweighed its benefits. The final implementation uses SQLAlchemy's `Base.metadata.create_all()` method, which is simpler and more robust for a demo project. This decision prioritized a working, demonstrable system over adherence to a specific tool that was proving problematic.

2.  **Application-Level Retry Logic:** To solve the startup race condition, a robust retry mechanism was implemented directly within the FastAPI application's startup event using the `tenacity` library. This is a superior solution to a `docker-compose` healthcheck for this use case, as it makes the application itself resilient to temporary database unavailability, a common scenario in distributed systems.

3.  **Enum Implementation:** The `Enum` types for roles and permissions were defined in the SQLAlchemy models with `native_enum=False`. This instructs SQLAlchemy to create them as `VARCHAR` columns with `CHECK` constraints, which is a more portable and less problematic approach across different database backends compared to native `ENUM` types.

4.  **Dependency Injection for Security:** FastAPI's dependency injection system was heavily utilized to handle security. A `get_current_user` dependency protects all authenticated routes, while a more advanced `get_permission_checker` factory creates dependencies that check for specific role levels (e.g., Manager, Viewer), making the endpoint logic clean and declarative.

## Scope for Improvement

1.  **Re-introduce Production-Grade Migrations:** For a real production system, database migrations are non-negotiable. I would re-introduce Alembic, but with a more controlled setup, likely using a dedicated entrypoint script that waits for the DB and then runs `alembic upgrade head` before starting the main application server.

2.  **More Granular Permissions:** The current system links roles to departments. A more advanced implementation would use a full-fledged permissions model (e.g., using a Casbin or OpenFGA-style model) where permissions like `resource:read`, `resource:write` are assigned to roles, and roles are assigned to users. This decouples roles from a hardcoded hierarchy.

3.  **Centralized User Management / Invites:** The system currently lacks a user invitation flow. A production system would need endpoints for inviting users to an organization/department, which would create a temporary token and allow the new user to sign up and be automatically assigned the correct role.

4.  **Asynchronous Database Calls:** For higher performance, all database operations in the `crud.py` file could be made asynchronous using libraries like `asyncpg` for the database driver and making the FastAPI endpoint functions `async`.