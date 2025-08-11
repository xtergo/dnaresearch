
# DNA Research Platform – Full Vision & Implementation Blueprint
_Generated: 2025-08-11 06:48:25Z UTC_

> This document consolidates everything we planned in this chat: JSON‑first schemas, theory engine, theory dashboard, anchor/diff storage, gene lookup & visualization, sequencing‑partner integration, blockchain consent/audit, privacy & governance, costs, funding, and a pragmatic roadmap. It is structured so you can hand it to engineers and start building immediately.

---

## 1) Executive Summary

- **Mission:** Deliver a reproducible, privacy‑preserving, and cost‑efficient genomics platform that makes **small family datasets** useful while scaling to cohorts.  
- **Core ideas:**  
  1) **Theories‑as‑code (JSON)** with transparent priors/likelihoods and versioning (SemVer).  
  2) **Evidence accumulation** (Bayesian updating) from families/cohorts over time.  
  3) **Anchor+Diff storage** to minimize DB size and accelerate queries.  
  4) **Dual UX** (parent‑friendly summaries + researcher detail).  
  5) **Consent‑aware** analysis with immutable audit (permissioned blockchain).

**MVP (8–12 weeks)**: JSON schemas → API stub → anchor/diff storage → theory runner (Robot/Python) → gene search/interpret → partner webhook ingest → nightly recompute → basic theory dashboard.

---

## 2) Personas & Use Cases

**Personas**: Parent/Citizen · Immunology/ASD Researcher · Sequencing Partner · Nonprofit Operator.  
**Use cases**: Family ASD insights · Cross‑time/provider comparisons · Gene lookup & interpretation · Create/fork theories · Probabilistic updates · Consent‑aware research.

---

## 3) JSON‑First Artifacts (Schemas & Examples)

All artifacts validate with JSON Schema 2020‑12. (See repo `schemas/`.)

### 3.1 Hierarchy (“Linné++”)
Probabilistic DAG from particles → atoms/minerals → molecules → life → human/DNA. Multiple versions, never 100% certainty.

Key: `id`, `version`, `lifecycle`, `nodes[id,type,label,prior<1]`, `edges[from,to,rel,prior<1]`, `provenance{created_by,created_at,updated_at,sources[]}`.

### 3.2 Theory (Executable)
`id`, `version`, `scope`, `compat.hierarchies[]`, `criteria` (genes/pathways/phenotypes/axioms), `evidence_model` (likelihood weights, priors, null model), `outputs` (BF/Posterior/SupportClass).

### 3.3 Evidence (NDJSON)
Items like `variant_hit`, `segregation`, `pathway` with weights and timestamps; attached to a specific theory version and family/dataset.

### 3.4 Run Request/Result
- Request: theory@ver, hierarchy@ver, dataset (family: VCFs), flags (privacy).  
- Result: metrics, BF, posterior_family, diagnostics, artifact hash (sha256).

### 3.5 Gene Object & Interpretation
`id/symbol/location`, pathways, protein domains, summaries (parent vs researcher), evidence (phenotype links), interpretation rules, provenance, `confidence<1`.

---

## 4) Storage Strategy – Hierarchical Anchors + Diffs

**Anchors**: Species → Population/Lineage → Family → IndividualRef (IR).  
Children store **Δ (diffs)** vs nearest anchor: SNV/indel/SV, coverage masks, QC aggregates.  
**Auto‑promotion**: promote a new anchor when delta/quality/popularity thresholds are met; rebase children; GC old diffs (ledger keeps hashes).

**Materialization**: Resolve sequence/variants by walking `Root → … → NearestAnchor → Δ… → Target`, only touching relevant blocks.  
**Performance**: warm cache ~1.05–1.2× baseline; cold ~1.2–1.8× baseline; greatly reduced I/O.

**Policy (JSON)**: thresholds for delta_bp, quality gain, error drop, min members, with operator approval gate.

---

## 5) Theory Engine – Bayesian Updating

`BF_family = P(data | theory) / P(data | null)`;  
Global posterior: `Posterior = (Prior * Π BF_i) / (Prior * Π BF_i + (1-Prior))`, with shrinkage for small N.  
**Outputs**: Posterior; Support class (Weak/Moderate/Strong); Diagnostics (what moved the needle).  
**Federated mode**: local compute, upstream only BF/aggregates (privacy‑preserving).

Robot Framework test suite wraps Python keywords for repeatability; every change produces an auditable run artifact (hash).

---

## 6) Theory Dashboard – Product Spec

### 6.1 Default & Filters
- Default sort: **Posterior desc** (tie‑break: evidence count → recency).  
- Filters: text search, tags (manual + AI), scope (e.g., **autism**), lifecycle, author, date, evidence count, “has comments”.

### 6.2 Tagging
- Manual tags by author (Robot tags under the hood).  
- **AI autotagging**: embeddings + zero‑shot; stored as `{tag, confidence}`; UI badge “AI”.

### 6.3 Scheduled Recompute
- Nightly cron (`0 2 * * *`) and incremental triggers when evidence/data/theory changes.  
- Incremental graph recompute to avoid thundering herd.

### 6.4 Fork/Derive & “Stronger” Theories
- Fork from parent → lineage edge; child is “stronger” if `Posterior_child > Posterior_parent + ε` and/or `BF_child/BF_parent ≥ τ` on overlapping families.  
- Explainability panel shows deltas (new evidence, criteria changes).

### 6.5 Comments & Collaboration
- Threaded markdown comments; reactions; @mentions; moderation and flagging.

### 6.6 Versioning & Quotas
- **Auto SemVer**: PATCH (typos/meta), MINOR (criteria additions non‑relaxing), MAJOR (criteria/evidence_model/compat changes).  
- Quotas: Free N theories; Pro 10×; Enterprise 100×. Exceeding → block create, show upsell; deletion = hide → archive subsystem (immutable, restorable).

### 6.7 Dependencies & Impact
- Show “Inherits from” and “Used by” DAG; impact preview reveals affected dependents before publishing.

**API additions**: list/filter/sort (`GET /theories`), details (`GET /theories/{id}`), history (`/history`), create/update/fork, tags, comments, compare, schedule recompute.

---

## 7) Gene Search & Visualization

- `GET /genes/search?query=` (symbol/alias/position)  
- `GET /genes/:id` (summaries for parent/researcher)  
- `POST /genes/:id/interpret` (variants → impact summary + confidence)  
- `GET /dna/visualize?chr=…&start=…&end=…` (zoomable browser: chromosome → gene → exon/intron → base; overlays: variants, time, provider).  
- Comparison: provider A vs B; time1 vs time2; highlight diffs.

---

## 8) Sequencing‑Partner Integration

**Order flow**: place order → partner ships kit → on completion partner uploads (pre‑signed URLs) or posts webhook → ingest: QC → diff vs anchor → DB insert → ledger write → notify user.  
**Security**: TLS, checksums, optional PGP.  
**Consent capture** on order; discount if donating anonymized data to research.

---

## 9) Consent, Privacy, and Blockchain

- **On‑chain** (permissioned ledger): `{hash, owner DID, consent_policy hash, lifecycle, provenance, signatures}`.  
- **Off‑chain**: encrypted DNA artifacts (S3/MinIO; AES‑256, KMS/HSM).  
- **Right‑to‑be‑forgotten**: delete off‑chain, mark on‑chain as revoked.  
- Periodic **public anchor** (Merkle root) to a public chain for timestamping.

RBAC/ABAC + OPA/Rego policies; PII isolated in a vault; tokenization at app layer.

---

## 10) Cloud Architecture & Costing (ref)

- API (FastAPI), DB (Postgres), object storage (S3/MinIO), cache (Redis), queue (SQS/RQ), ledger (Fabric/Quorum).  
- **100 users · 2 TB**: ≈ **900–1,100 USD/month** (can be 500–700 with optimization).  
- Storage with Anchor/Diff: 20–80 MB/person (typical 40 MB).

---

## 11) Funding & Business Model (Nonprofit + Licensing)

- **Grants**: national (e.g., Vetenskapsrådet, Vinnova) and EU (Horizon), foundations (Wallenberg, Wellcome).  
- **Partnerships**: universities/biobanks; cloud credits (nonprofit programs).  
- **Crowdfunding & memberships** for public engagement.  


---



## 13) Roadmap

### Sprint 1–2 (Weeks 1–4) – MVP Core
- Schemas + validators; Anchor/Diff lib; minimal API; gene lookup; parent/researcher report; run ledger hashing.

### Sprint 3–4 (Weeks 5–8) – Integrations
- Sequencing webhook; first partner pilot; theory runner (Robot/Python) with Bayes; Redis cache; basic ledger.

### Sprint 5–6 (Weeks 9–12) – Hardening
- Federated mode; DP aggregates; anchor auto‑promotion; UI polish; monitoring/alerts; backup & DR; security review.

### Long‑Term (6–18 months)
- Multi‑omics; protein/network simulations; cohort dashboards; i18n; certifications.

---

## 14) Governance, Compliance, Risk

- GDPR DPIA; consent logs; breach procedures; data minimization.  
- Ethics advisory board; transparency reports.  
- Risks: re‑identification (mitigate via DP & access control); model overconfidence (never 100%); vendor lock‑in (IaC + portability).

---

## 15) Testing, CI/CD, Quality

- Pre‑commit JSON validation, deterministic hashing, unit tests.  
- CI synthetic genomes; regression suites; randomized materialization audits.  
- Reproducibility: artifact hashes in reports; environment pinning.

---

## 16) KPIs

- Time‑to‑insight (family run) < 2 min (warm cache).  
- Storage per person: 20–80 MB (target 40 MB).  
- Posterior recompute latency < 30 s after ingest.  
- Consent verification latency < 1 s.

---

## 17) Public API (Draft Highlights)

**Core**: `POST /runs`, `POST /posterior/update`, `GET /theories/:id@ver`, `GET /hierarchies/:id@ver`, `POST /evidence`, `GET /reports/:id`  
**Storage**: `POST /ref/build|diff|rebase`, `GET /materialize`, `GET /ref/compare`  
**Genes & Viz**: `GET /genes/search`, `GET /genes/:id`, `POST /genes/:id/interpret`, `GET /dna/visualize`  
**Partners**: `POST /orders`, `POST /ingest/webhook`, `POST /files/presign`  
**Ledger**: `POST /ledger/record`, `POST /ledger/consent`, `GET /ledger/verify`

---

## 18) Appendix – Practical Heuristics

- **Family differences**: parent‑child tens of de novo variants; siblings ~1.5–2.5 Mb SNV differences.  
- **Cross‑species diffs**: great apes tens of Mb; mammals hundreds of Mb+ (alignable portions).  
- **Performance**: cold path ~1.2–1.8× vs raw; warm ~1.05–1.2×; reduced I/O dominates.

---

**End of document.**
