# Pathlight Project Structure

```
pathlight/
├── apps/                       # Mỗi service có thể scale / deploy độc lập (K8s)
│   ├── api-gateway/            # FastAPI GraphQL / REST, auth, rate-limit
│   │   └── src/
│   ├── agent-hub/              # Multi-Agent Orchestrator (planning/execution)
│   │   └── src/                # LangChain agents, tool-registry, memory adapter
│   ├── content-worker/         # Celery tasks: ingestion, lesson-gen, grading
│   ├── scheduler/              # APScheduler / Celery beat: quest, reminder
│   ├── realtime/               # Socket.io gateway + presence
│   ├── analytics-api/          # FastAPI phục vụ KPI, BI query
│   └── web/                    # Next.js + shadcn/ui (SSR & App Router)
├── packages/                   # Code share dưới dạng Python/TS workspace
│   ├── ai_core/                # Wrapper LlamaIndex, RAG, prompt templates
│   ├── agents/                 # Generic skills, planning-strategy, reflexion
│   ├── skill_graph/            # Ontology & tagging (Bloom, CEFR)
│   ├── gamification/           # XP, quest engine, badge logic
│   ├── models/                 # Pydantic & Zod schema dùng chung
│   └── ui/                     # React component library chia sẻ cho FE
├── pipelines/                  # Data / ML workflows
│   ├── ingestion/              # OCR → splitter → embed → Milvus
│   ├── evaluation/             # offline rubric scoring, model benchmark
│   └── finetune/               # LoRA/fine-tune script, dataset curation
├── infra/                      # IaC & manifest
│   ├── terraform/              # GKE, CloudSQL, S3-compatible storage
│   ├── helm/                   # Charts cho từng app, Milvus, Postgres
│   ├── k8s/                    # Kustomize overlays (dev/stg/prod)
│   └── observability/          # Prometheus, Grafana, Loki, OpenTelemetry
├── configs/                    # config *.yaml, .env.example, prompt-config
├── scripts/                    # CLI helper: db-migrate, load-test, seed-data
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                    # Playwright + scenarios từ Use-case Spec
├── docs/                       # PRD, ADR, API spec (OpenAPI & GraphQL)
│   ├── proposal.pdf
│   ├── use-cases/
│   └── adr/
├── .github/
│   └── workflows/              # build-test-lint → push images → ArgoCD sync
└── README.md                   # setup local (Tilt / docker-compose), coding-style
```
