# OpenWorker Engineering Extension

## Goal

Turn OpenWorker into an engineering-work coordinator without forking domain algorithms into the OpenWorker core.

OpenWorker remains responsible for:

- agent/session orchestration;
- model routing;
- permissions and approval boundaries;
- connectors, MCP, messaging, and automation;
- workspace/file interaction;
- progress and deliverable coordination.

Specialist repositories remain responsible for engineering-domain truth and algorithms.

## Architecture

```text
OpenWorker
  |
  +-- Engineering Coworker persona
  |
  +-- coworker.engineering adapter boundary
          |
          +-- Knowledge Graph / Semantic Engine
          +-- AI-EngSketch / drawing generation
          +-- PCCES / quantity and cost
          +-- DWG/DXF -> semantic drawing -> IFC/BIM/3D
          +-- Structural calculation / Calculation Trace
          +-- PERT/CPM scheduling
          +-- Technical-report and evidence-chain services
          +-- Visualization/media services
```

Each integration should expose the same high-level contract:

1. identify itself and the capabilities it provides;
2. expose a health/readiness result;
3. accept a named operation plus a structured payload;
4. return a structured result containing provenance and artifacts where applicable.

The transport is deliberately not fixed. An adapter may use MCP, HTTP, CLI, or a Python package. This lets domain projects evolve independently and keeps upstream OpenWorker merges manageable.

## Traceability contract

Engineering workflows should preserve this chain whenever possible:

```text
source artifact
  -> normalized input
  -> assumptions / constraints
  -> specialist operation
  -> calculation or transformation trace
  -> result
  -> deliverable artifact
```

Results should distinguish:

- source facts;
- user assumptions;
- inferred/normalized data;
- calculated values;
- warnings and unresolved uncertainties;
- produced files or external artifact identifiers.

## Upstream compatibility rules

1. Prefer additions under `coworker/engineering/`, `docs/engineering/`, and engineering-specific personas.
2. Avoid editing `coworker/engine.py`, core permission logic, or generic connector machinery unless an extension point is impossible.
3. Do not copy specialist-domain implementations into OpenWorker.
4. Keep adapter transport replaceable.
5. Add tests for adapter registry and persona loading before wiring real services.
6. Periodically compare this fork with `andrewyng/openworker:main` and resolve upstream drift before large feature batches.

## Integration order

### Phase E0 — Foundation

- Engineering Coworker persona.
- Adapter protocol and capability registry.
- Architecture and traceability contract.

### Phase E1 — Tool bridge

- Runtime tool facade for listing adapter capabilities, checking readiness, and invoking safe read-only operations.
- Configuration model for local/MCP/HTTP adapter endpoints.
- Unit tests and approval classification.

### Phase E2 — First specialist integrations

Start with capabilities that can provide deterministic structured results:

- engineering knowledge graph;
- engineering sketch/drawing;
- PCCES quantity/cost;
- structural calculation/Calculation Trace.

### Phase E3 — Drawing and BIM pipeline

- DWG/DXF ingestion;
- semantic normalization;
- IFC/BIM transformation;
- 3D/model artifact handoff;
- cross-link entities to the engineering knowledge graph.

### Phase E4 — Project controls

- PERT/CPM scheduling;
- quantities/cost/schedule cross-references;
- project-status evidence and reporting.

### Phase E5 — Engineering production coworker

- End-to-end workflow templates;
- human approval gates for consequential outputs;
- automated technical-report assembly;
- reusable project memory and engineering evidence chains.

## Definition of done for an integration

An adapter is not considered integrated merely because OpenWorker can call it. It must have:

- health/readiness reporting;
- structured input/output schema;
- provenance/evidence fields;
- error and timeout behavior;
- tests;
- documented approval requirements;
- at least one end-to-end workflow producing a real artifact.
