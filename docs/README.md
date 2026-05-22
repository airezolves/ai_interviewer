# InterviewKit AI — Documentation Index

## Docs Overview

| Doc | Description |
|-----|-------------|
| [01_ARCHITECTURE.md](01_ARCHITECTURE.md) | Full microservices architecture, service breakdown, data flow, tech stack |
| [02_ROADMAP.md](02_ROADMAP.md) | End-to-end phased roadmap with sprint tasks, metrics, and decision points |
| [03_TEAM_DIVISION.md](03_TEAM_DIVISION.md) | Task assignment for 3-person team (DS1, DS2, FE1) with day-by-day plan |
| [04_MVP_SPEC.md](04_MVP_SPEC.md) | MVP scope, user flow, DB schema, API endpoints, cost estimate |
| [05_SERVICE_DESIGN.md](05_SERVICE_DESIGN.md) | Detailed service internals, folder structure, patterns, Docker Compose |

## Graphviz DOT Files

Render with: `dot -Tpng <file>.dot -o <file>.png`

| File | Description |
|------|-------------|
| [mvp_architecture.dot](mvp_architecture.dot) | Service topology and connections |
| [mvp_pipeline.dot](mvp_pipeline.dot) | Kit generation pipeline (parallel execution) |
| [mvp_features.dot](mvp_features.dot) | Feature dependency graph |
| [service_communication.dot](service_communication.dot) | Inter-service communication patterns |
| [roadmap_timeline.dot](roadmap_timeline.dot) | Full timeline with team assignments |

## Quick Start

```bash
# Render all DOT files to PNG
for f in docs/*.dot; do dot -Tpng "$f" -o "${f%.dot}.png"; done
```

## Team Quick Reference

- **DS1:** Gateway, Auth, Resume Service, Kit Orchestrator, Export Service
- **DS2:** AI Engine Service (all LLM/prompt work)
- **FE1:** Frontend (Next.js + TypeScript)

## Key Decisions

1. **Python for all backend** — FastAPI async, excellent LLM library support
2. **TypeScript for frontend** — Next.js 14, type safety, great DX
3. **Microservices from Day 1** — Clear boundaries, independent deployment, team parallelism
4. **PostgreSQL + Redis** — Proven, reliable, free tiers available
5. **Claude API primary, GPT-4 fallback** — Best structured output quality
6. **SSE for streaming** — Simpler than WebSockets, sufficient for one-way progress
