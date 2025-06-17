# Libs Folder Overview 📦

## Folder Purpose 🎯
Shared Python and TypeScript packages used by the services and frontend.

## Full Directory Tree
```text
libs/
  ├── ai-prompts/
  │   ├── README.md
  │   ├── pyproject.toml
  │   └── prompts/
  │       └── __init__.py
  ├── common-types-py/
  │   ├── README.md
  │   └── pyproject.toml
  ├── common-types-ts/
  │   ├── README.md
  │   ├── package.json
  │   ├── tsconfig.json
  │   └── src/
  │       └── index.ts
  ├── common-utils-py/
  │   ├── README.md
  │   ├── pyproject.toml
  │   └── utils/
  │       ├── __init__.py
  │       ├── logger.py
  │       └── retry.py
  └── common-utils-ts/
      ├── README.md
      ├── package.json
      ├── tsconfig.json
      └── src/
          ├── logger.ts
          └── retry.ts
```

## Item-by-Item Table
| Path | Role |
| --- | --- |
| ai-prompts/ | Placeholder package for shared AI prompt templates. |
| ai-prompts/README.md | (empty) documentation stub. |
| ai-prompts/pyproject.toml | Python package configuration. |
| ai-prompts/prompts/__init__.py | Package initializer. |
| common-types-py/ | Python type stubs shared across services. |
| common-types-py/README.md | (empty) documentation stub. |
| common-types-py/pyproject.toml | Package metadata. |
| common-types-ts/ | TypeScript type definitions. |
| common-types-ts/README.md | (empty) documentation stub. |
| common-types-ts/package.json | Node package metadata. |
| common-types-ts/tsconfig.json | TS compiler options. |
| common-types-ts/src/index.ts | Type definitions entry point. |
| common-utils-py/ | Python helper utilities. |
| common-utils-py/README.md | (empty) documentation stub. |
| common-utils-py/pyproject.toml | Package configuration. |
| common-utils-py/utils/__init__.py | Package initializer. |
| common-utils-py/utils/logger.py | Logging helpers (empty). |
| common-utils-py/utils/retry.py | Retry utilities (empty). |
| common-utils-ts/ | TypeScript helper utilities. |
| common-utils-ts/README.md | (empty) documentation stub. |
| common-utils-ts/package.json | Node package metadata. |
| common-utils-ts/tsconfig.json | TS compiler options. |
| common-utils-ts/src/logger.ts | Logging helpers (empty). |
| common-utils-ts/src/retry.ts | Retry utilities (empty). |

## Key Workflows / Entry Points
- Install Python libs locally with `pip install -e libs/common-utils-py`.
- Use `npm install` inside TypeScript packages when developing.
- Packages can be imported from services or the frontend.

## Example Usage
```bash
# Example: install Python utilities in editable mode
pip install -e libs/common-utils-py
```

## Development Tips
- Keep TypeScript and Python types in sync when both exist.
- Add unit tests before publishing libraries.

## TODO
- TODO: flesh out utility functions and type definitions.
