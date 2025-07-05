# Services Folder Overview 🛠️

## Folder Purpose 🎯
Collection of FastAPI microservices that power the platform APIs.

## Full Directory Tree
```text
services/
  ├── auth-service/
  │   ├── Dockerfile
  │   ├── alembic.ini
  │   ├── pyproject.toml
  │   ├── alembic/
  │   │   ├── README
  │   │   ├── env.py
  │   │   └── script.py.mako
  │   └── src/
  │       └── .gitkeep
  ├── course-service/
  │   ├── Dockerfile
  │   ├── alembic.ini
  │   ├── pyproject.toml
  │   ├── alembic/
  │   │   ├── README
  │   │   ├── env.py
  │   │   └── script.py.mako
  │   └── src/
  │       └── .gitkeep
  ├── lesson-service/
  │   ├── Dockerfile
  │   ├── alembic.ini
  │   ├── pyproject.toml
  │   ├── alembic/
  │   │   ├── README
  │   │   ├── env.py
  │   │   └── script.py.mako
  │   └── src/
  │       └── .gitkeep
  ├── test-service/
  │   ├── Dockerfile
  │   ├── alembic.ini
  │   ├── pyproject.toml
  │   ├── alembic/
  │   │   ├── README
  │   │   ├── env.py
  │   │   └── script.py.mako
  │   └── src/
  │       └── .gitkeep
  └── user-service/
      ├── Dockerfile
      ├── alembic.ini
      ├── pyproject.toml
      ├── alembic/
      │   ├── README
      │   ├── env.py
      │   └── script.py.mako
      └── src/
          └── .gitkeep
```

## Item-by-Item Table
| Path | Role |
| --- | --- |
| api-gateway/ | Gateway routing requests to services. |
| api-gateway/Dockerfile | Container build instructions. |
| api-gateway/requirements.txt | Python dependencies for gateway. |
| api-gateway/src/.gitkeep | Placeholder for gateway code. |
| auth-service/ | Authentication microservice skeleton. |
| auth-service/Dockerfile | Build file for auth service. |
| auth-service/alembic.ini | Alembic configuration. |
| auth-service/pyproject.toml | Python package metadata. |
| auth-service/alembic/README | Alembic usage notes. |
| auth-service/alembic/env.py | Migration environment. |
| auth-service/alembic/script.py.mako | Migration template. |
| auth-service/src/.gitkeep | Placeholder for service code. |
| course-service/ | Course management microservice skeleton. |
| course-service/Dockerfile | Build file for course service. |
| course-service/alembic.ini | Alembic configuration. |
| course-service/pyproject.toml | Python package metadata. |
| course-service/alembic/README | Alembic usage notes. |
| course-service/alembic/env.py | Migration environment. |
| course-service/alembic/script.py.mako | Migration template. |
| course-service/src/.gitkeep | Placeholder for service code. |
| lesson-service/ | Lesson management microservice skeleton. |
| lesson-service/Dockerfile | Build file for lesson service. |
| lesson-service/alembic.ini | Alembic configuration. |
| lesson-service/pyproject.toml | Python package metadata. |
| lesson-service/alembic/README | Alembic usage notes. |
| lesson-service/alembic/env.py | Migration environment. |
| lesson-service/alembic/script.py.mako | Migration template. |
| lesson-service/src/.gitkeep | Placeholder for service code. |
| test-service/ | Testing microservice skeleton. |
| test-service/Dockerfile | Build file for test service. |
| test-service/alembic.ini | Alembic configuration. |
| test-service/pyproject.toml | Python package metadata. |
| test-service/alembic/README | Alembic usage notes. |
| test-service/alembic/env.py | Migration environment. |
| test-service/alembic/script.py.mako | Migration template. |
| test-service/src/.gitkeep | Placeholder for service code. |
| user-service/ | User management microservice skeleton. |
| user-service/Dockerfile | Build file for user service. |
| user-service/alembic.ini | Alembic configuration. |
| user-service/pyproject.toml | Python package metadata. |
| user-service/alembic/README | Alembic usage notes. |
| user-service/alembic/env.py | Migration environment. |
| user-service/alembic/script.py.mako | Migration template. |
| user-service/src/.gitkeep | Placeholder for service code. |

## Key Workflows / Entry Points
- Build each service with `docker build -t <name> services/<service>`.
- Run database migrations via `alembic upgrade head` inside a service dir.
- Services will eventually expose FastAPI apps run with Uvicorn.

## Example Usage
```bash
# Build the user service container
cd services/user-service
docker build -t user-service .
```

## Development Tips
- Python 3.12 is expected for service code.
- Use Alembic for schema migrations.
- Implement FastAPI apps under each `src` directory.

## TODO
- TODO: flesh out service implementations and add tests.
