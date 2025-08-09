# PathLight \- Adaptive AI Learning Platform

<p align="center">
  <img src="docs/architecture.png" alt="Architecture" width="640" />
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-orange" alt="License" /></a>
  <img src="https://img.shields.io/badge/Status-Alpha-red" alt="Status" />
  <img src="https://img.shields.io/badge/Next.js-14-black" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-success" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Language-TypeScript%20%7C%20Python-blue" alt="Languages" />
</p>

> PathLight is a modular platform for building adaptive, AI‑powered self‑learning experiences: ingest arbitrary content, auto‑generate learning paths, quizzes & progress analytics, and motivate learners with gamification.

---
## Table of Contents
- [Key Value Proposition](#key-value-proposition)
- [Feature Matrix](#feature-matrix)
- [Monorepo Structure](#monorepo-structure)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
  - [Frontend (Next.js)](#frontend-nextjs)
  - [Python Services](#python-services)
- [Development Workflow](#development-workflow)
- [Configuration](#configuration)
- [Authentication Flow](#authentication-flow)
- [UI & UX Principles](#ui--ux-principles)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---
## Key Value Proposition
| Problem | PathLight Approach | Outcome |
| ------- | ------------------ | ------- |
| Learners lose direction | Dynamic learning path & reminders | Consistent study habits |
| Static content gets stale | On‑demand generation (lessons, quizzes) | Fresher personalized material |
| Low engagement | XP, levels, rankings, activity heatmap | Higher retention |
| Manual analytics effort | Unified dashboard & per‑user telemetry | Faster iteration |

---
## Feature Matrix
| Domain | Capabilities (Implemented / Planned) |
| ------ | ------------------------------------ |
| Content Ingestion | Upload documents & media (scaffold for RAG) |
| User Profiles | Editable profile, avatar upload, level & XP stats |
| Dashboard | Stats grid, leaderboard, activity heatmap |
| Quizzes | Creation workflow (UI scaffolding) & submission pipeline (planned) |
| Courses | Course creation & enrollment (planned microservice) |
| Gamification | XP, levels, rank placeholders (extensible) |
| Authentication | Email/password, Google OAuth hook, session & remember‑me cookies |
| Security | Strict SameSite cookies, token expiry handling, middleware guards |
| Observability | Hooks prepared for client metrics (backend expansion planned) |

---
## Monorepo Structure
```
pathlight/
  README.md
  docs/                # Design & reference docs
  frontend/            # Next.js 14 application (UI + client logic)
  services/            # FastAPI microservice skeletons
  libs/                # Shared TS & Python packages (types, utils, prompts)
  LICENSE
```
### Notable Frontend Modules
- `src/app/user/dashboard` – Dashboard entry (auth‑guarded).
- `src/components/user/profile` – Profile page hooks, avatar upload, form logic.
- `middleware.ts` – Central auth & redirect logic (token expiry + protected routes).
- `src/utils/api.ts` – Fetch wrapper (cookie‑based auth, unified response shape).
- `src/lib/api` – Layered API client (auth / user / quiz / course groups).

### Services (Scaffolds)
Auth, User, Course, Quiz, Lesson, Test, Agentic. Each includes Dockerfile + Alembic config to accelerate domain rollout.

### Shared Libraries (libs/)
Common types & utilities (Python + TypeScript) and prompt templates; designed for publishing or internal linking.

---
## Technology Stack
| Layer | Tools |
| ----- | ----- |
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS, shadcn/ui |
| State / Hooks | Custom React hooks per domain (auth, dashboard, profile) |
| Styling | Utility‑first Tailwind with design tokens and subtle shadows |
| Backend (planned & scaffold) | FastAPI, Pydantic, PostgreSQL, Alembic |
| Auth | JWT (cookie stored), Google OAuth hook, middleware guards |
| Build & Dev | Node 18+, pnpm/npm, Docker, Python 3.12 |
| DX | ESLint, TypeScript strict settings (configurable) |

---
## Quick Start
### Frontend (Next.js)
```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Start dev server
npm run dev  # http://localhost:3000
```
Optional environment variables (create `frontend/.env.local`):
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Python Services
Each service is currently a scaffold. Example workflow:
```bash
cd services/auth-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # or: pip install -e . if pyproject defined
alembic upgrade head             # run migrations when models exist
uvicorn src.main:app --reload    # after you implement FastAPI app
```

### Docker (example for a service)
```bash
docker build -t pathlight-auth services/auth-service
```

---
## Development Workflow
1. Branch naming: `feat/<scope>` `fix/<scope>` `chore/<scope>`.
2. Run lint & type checks before PR: `npm run lint` (frontend) / `ruff` + `mypy` (planned) for Python.
3. Keep architecture diagram updated when adding cross‑service contracts.
4. Favor small, vertical slices (UI + hook + API call together) for clarity.

---
## Configuration
| Area | Location | Notes |
| ---- | -------- | ----- |
| API Base URL | `frontend/src/config/env.ts` | Drives `API_CONFIG.BASE_URL` |
| Auth Cookies | `frontend/src/utils/cookies.ts` | Session vs remembered tokens |
| Middleware Guards | `frontend/middleware.ts` | Token expiry, route protection |
| API Layer | `frontend/src/utils/api.ts` & `src/lib/api` | Unified request helpers |

---
## Authentication Flow
1. User submits credentials (or Google OAuth) via `SignInForm`.
2. Successful response returns `access_token` → stored in secure cookie (`auth_token` or `session_token`).
3. Middleware validates presence & expiry on protected routes. Expired tokens are cleared and user redirected to `/auth/signin?redirect=...`.
4. Client hooks (`useAuth`, dashboard/profile hooks) perform secondary validation & optimistic UI gating.
5. Logout clears cookies and performs hard redirect to sign‑in.

---
## UI & UX Principles
- Minimal borders; rely on soft elevation (`shadow-sm`) and neutral backgrounds.
- Consistent 44px (h‑11) form control height for tap targets.
- Gradual disclosure: dashboards load skeletons / spinners while fetching.
- Responsive sidebar (collapsible desktop, overlay on mobile) with full‑fill active state for clarity.

---
## Roadmap
| Phase | Focus | Highlights |
| ----- | ----- | ---------- |
| 0 (Now) | Core UI + Auth | Profile, Dashboard, Basic Quiz stub |
| 1 | Content & Quiz Engine | Upload pipeline, question generation, grading service |
| 2 | Adaptive Sequencing | Skill model, personalized path orchestration |
| 3 | Analytics & Interventions | Early risk detection, notification service |
| 4 | Marketplace & Collaboration | Shared course publishing, versioning |

---
## Contributing
We welcome early feedback.
1. Open an issue describing enhancement or bug.
2. Fork → feature branch → PR against active branch (default: `main` or current tracked feature branch).
3. Provide clear test steps / screenshots.
4. Keep changes scoped; large refactors require a design issue first.

### Commit Message Style (Conventional)
```
feat(profile): add date picker to birth date field
fix(auth): clear expired cookie before redirect loop
```

---
## License
Released under MIT. See [LICENSE](LICENSE).

---
## Acknowledgements
Inspired by modern open learning platforms and the open‑source ecosystem that accelerates experimentation.

> Build purposefully. Learn continuously. Iterate transparently.
