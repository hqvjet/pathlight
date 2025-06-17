# PathLight – AI Tutor Platform 📚

[![Build](https://img.shields.io/github/actions/workflow/status/owner/repo/ci.yml?branch=main)](https://github.com/owner/repo/actions)
[![License](https://img.shields.io/github/license/owner/repo.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/owner/repo.svg)](https://github.com/owner/repo/commits/main)

## 📝 Overview
PathLight is an open-source platform for building adaptive AI tutors.
It blends language models, knowledge graphs and gamification to deliver
personalized learning experiences at scale.

## 💪 Key Features
- **Ingestion & RAG** – OCR → parser → FAISS/Milvus for fast retrieval.
- **Ontology & Skill Tagging** – map content via Bloom and CEFR taxonomies.
- **Learner Model & Adaptive Road-map** – track skills, recommend next steps.
- **Lesson Generation** – Gemma-27B text with DALL·E 3 artwork.
- **Assessment Suite** – MCQ, short-answer, and auto-grading workflows.
- **24 × 7 Chatbot Mentor** – contextual Q&A and study reminders.
- **Gamification Layer** – XP, quests, badges and mini games.
- **Analytics Dashboard & A/B Testing** – iterate on content and UX.
- **Compliance & Privacy** – PII encryption and copyright controls.

## 💡 Tech Stack
| Layer | Tech | Notes |
|-------|------|-------|
| **Backend** | Python 3.12.1, FastAPI, Pydantic | API services |
| **DB** | PostgreSQL 15 | relational store |
| **Vector DB** | FAISS (self-host) ⇒ Milvus (scale-out) | retrieval engine |
| **AI Orchestration** | LangChain / LlamaIndex, Ollama | LLM pipelines |
| **Task Queue** | Celery + Redis | async jobs |
| **Frontend** | Next.js, TailwindCSS, shadcn/ui | web app |
| **Realtime** | Socket.io / Supabase Realtime | presence & updates |
| **DevOps** | Kubernetes (GKE), Terraform, GitHub Actions → ArgoCD | CI/CD |
| **Observability** | Prometheus, Grafana, Loki | metrics & logs |

## 📊 Architecture
![Architecture Diagram](docs/architecture.png)

## 📚 Getting Started
### Prerequisites
- Docker ≥ 24
- `make`
- Node 18 LTS
- Python 3.12.1

### Quick Start
<details><summary>Run in Docker</summary>

```bash
git clone https://github.com/owner/repo.git
cd repo
make dev
```
Then open `http://localhost:3000`.
</details>

### Manual Setup
<details><summary>Local Development</summary>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/api-gateway/requirements.txt
export $(cat .env | xargs)
# Database and other services
# ...
cd frontend
npm install
npm run dev
```
</details>

## 📁 Folder Structure
```text
pathlight/
├── services/             # FastAPI microservices
│   ├── api-gateway/
│   ├── auth-service/
│   ├── course-service/
│   ├── lesson-service/
│   ├── test-service/
│   └── user-service/
├── libs/                 # Shared packages
│   ├── ai-prompts/
│   ├── common-types-py/
│   ├── common-types-ts/
│   ├── common-utils-py/
│   └── common-utils-ts/
├── frontend/             # Next.js app
├── docs/                 # diagrams & specifications
└── LICENSE
```

## 🙌 Contributing
1. Fork and clone this repo.
2. Create feature branches and open PRs against `main`.
3. Follow commit lint rules and run pre-commit (ruff + black).
4. Issues are labeled `bug`, `feat`, `task` and `help wanted`.

## 🎓 License
This project is released under the [MIT](LICENSE) license. You may replace or
extend it to suit your organization.

## 🎉 Acknowledgements
- Gemma, DALL·E 3 and other LLM models.
- Open-source libraries and the wider community.

<!-- TODO: add real architecture diagram and expand docs -->
