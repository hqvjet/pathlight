# Pathlight Project Structure

```
pathlight/
├── services/                   # Each microservice deployable independently
│   ├── api-gateway/            # FastAPI GraphQL / REST entrypoint
│   │   └── src/
│   ├── analytics-api/          # KPI & BI queries
│   ├── auth/                   # Authentication service
│   │   └── src/
│   ├── content-worker/         # Celery tasks for content processing
│   ├── scheduler/              # APScheduler / Celery beat jobs
│   ├── realtime/               # Socket.io gateway + presence
│   └── web/                    # Next.js frontend
├── libs/                       # Shared Python/TS packages
│   ├── skill_graph/            # Ontology & tagging (Bloom, CEFR)
│   ├── gamification/           # XP, quest engine, badge logic
│   ├── models/                 # Pydantic & Zod schema
│   └── ui/                     # React component library
├── infra/                      # IaC & manifests
│   ├── terraform/              # GKE, CloudSQL, object storage
│   ├── helm/                   # Helm charts for each service
│   ├── k8s/                    # Kustomize overlays (dev/stg/prod)
│   └── observability/          # Prometheus, Grafana, Loki, OpenTelemetry
├── configs/                    # YAML configs and .env examples
├── scripts/                    # CLI helpers: db-migrate, seed-data
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                    # Playwright scenarios from use cases
├── docs/                       # PRD, ADR, API specs
│   ├── proposal.pdf
│   ├── use-cases/
│   └── adr/
├── .github/
│   └── workflows/              # build-test-lint → push images → ArgoCD sync
└── README.md
```
