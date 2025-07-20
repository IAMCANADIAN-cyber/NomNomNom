# 1. Vision & Value Proposition

**Goal:** Locally ingest *arbitrary* large, heterogeneous datasets (≥1M tokens; mixed file types) and produce **task‑aware, loss‑bounded, 4K token “capsules”** that preserve salient facts, structure, anomalies, and representative exemplars—ready for an LLM with a 4K context window.

**Core Principles:**

1. **Task-Aware** (don’t summarize blindly; compress after knowing the user’s intent).
2. **Multi-View Representation** (statistical, structural, semantic, exemplars).
3. **Faithful & Auditable** (every summary bullet has provenance pointers).
4. **Progressively Expandable** (stub IDs let you drill deeper without re‑ingesting).
5. **Local & Private** (LM Studio + local embeddings; optional sanitization).
6. **Adaptive Compression** (dynamically balance modalities under token budget).

---

# 2. End-to-End Pipeline Overview

```
Folder Path
   ↓
Discovery & De-dup (hash, classify)
   ↓
Type-Specific Extraction / Normalization
   ↓
Chunking (L0) with Modality Tags
   ↓
Profiling & Multi-View Representations:
   - Embeddings (text, image CLIP, table semantic)
   - Column stats, log templates, entity graph
   - OCR & captions, code AST metrics
   ↓
Hierarchical Summaries (L1/L2/L3) via Extractive + Abstractive (LM Studio)
   ↓
User Task / Query
   ↓
Relevance & Coverage Retrieval (multi-index + MMR)
   ↓
Adaptive Compression Stack (aggregation, fusion, dedup, glossaries)
   ↓
4K Capsule Assembly (with stubs & provenance)
   ↓
Optional Expansion Requests (stub → retrieve & re-summarize)
```

---

# 3. Core Functional Modules

| Module                  | Responsibility                                         | Key Inputs          | Outputs                              |
| ----------------------- | ------------------------------------------------------ | ------------------- | ------------------------------------ |
| Discovery & Routing     | Traverse folder, classify files                        | Paths               | File metadata records                |
| Extraction              | Per-type text / structure / features                   | File path           | Canonical text, stats, captions, OCR |
| Chunking                | Create L0 chunks (400–800 tokens or modality-adjusted) | Canonical elements  | Chunk records                        |
| Representation Store    | Persist vectors, stats, entities, relationships        | Chunks + metadata   | SQLite / vector index                |
| Hierarchical Summarizer | Build L1–L3 compressed layers                          | Chunks & clusters   | Layered summaries                    |
| Query Interpreter       | Expand task semantics                                  | User task           | Expanded terms, facet hints          |
| Retriever & Scorer      | Select relevance + novelty balanced pool               | Task + indices      | Candidate chunk set                  |
| Compression Engine      | Apply structured reductions                            | Selected pool       | Compressed segments                  |
| Capsule Assembler       | Construct final context (≤4K tokens)                   | Compressed segments | Capsule text                         |
| Provenance Tracker      | Map summaries → source chunks                          | Summaries           | Mapping table                        |
| Expansion Manager       | Handle stub expansions                                 | Stub IDs            | Incremental capsule delta            |
| Evaluation Harness      | Fidelity, coverage, redundancy metrics                 | Store + capsule     | Reports                              |

---

# 4. File Type Handling & Modality Mapping

| File Type              | Techniques                                  | Modalities Produced               |
| ---------------------- | ------------------------------------------- | --------------------------------- |
| TXT / MD / HTML        | Clean, paragraph segmentation               | text                              |
| PDF (structured)       | Text layout + headings                      | text                              |
| PDF (scanned)          | OCR (Tesseract/PaddleOCR)                   | ocr\_text                         |
| DOCX / PPTX            | python-docx / python-pptx                   | text, slide                       |
| XLSX / CSV             | Streaming profiling (DuckDB/pandas)         | table\_stats, table\_exemplars    |
| JSON / NDJSON          | Schema flatten + key freq                   | schema, exemplar                  |
| LOG                    | Template mining (Drain) + anomalies         | log\_template, log\_anomaly       |
| Images (PNG/JPG)       | pHash, OCR (optional), caption (BLIP/LLaVA) | caption, ocr\_text, image\_vector |
| Code (optional)        | AST metrics, docstrings                     | code\_meta, code\_snippet         |
| Audio/Video (optional) | Whisper transcript + keyframe captions      | transcript, caption               |

---

# 5. Data Model (Logical Schema)

### 5.1 Tables (SQLite)

**files**
`file_id, path, type, subtype, size_bytes, mtime, content_hash, status, meta_json`

**chunks**
`chunk_id, file_id, modality, level (0/1/2/3), token_len, text, meta_json`

**embeddings**
`embedding_id, chunk_id, modality, model, dim, vector (blob)`

**images**
`image_id, file_id, phash, width, height, meta_json, clip_vector_ref`

**tables\_meta**
`table_id, file_id, sheet_name, n_rows, n_cols, profile_json`

**entities**
`entity_id, surface_form, canonical_form, type, freq, meta_json`

**entity\_chunk**
`entity_id, chunk_id, count`

**clusters**
`cluster_id, level, modality, member_chunk_ids (JSON), meta_json`

**summaries**
`summary_id, cluster_id, level, text, model, token_len, provenance_chunk_ids (JSON)`

**llm\_cache**
`cache_id, key_hash, request_json, response_text, input_tokens, output_tokens, created_at`

**capsules**
`capsule_id, task_hash, created_at, token_len, text, section_index_json`

**stubs**
`stub_id, capsule_id, reference_type (cluster|image|table|log|entity), reference_id, description`

**evaluation\_runs**
`run_id, capsule_id, metrics_json, created_at`

---

# 6. Chunking & Hierarchy Strategy

| Level | Generation Method                                   | Target Tokens / Node |
| ----- | --------------------------------------------------- | -------------------- |
| L0    | Raw segmented pieces (semantic / page / template)   | 200–800              |
| L1    | Extractive: top sentences + key metrics per cluster | 80–150               |
| L2    | Abstractive fusion (LM Studio) over L1 groups       | 100–180              |
| L3    | Global abstractive synthesis over L2 summaries      | 300–350              |

**Clustering:**

* Use embeddings per modality (text model; CLIP for images).
* Choose k adaptively (e.g., k ≈ sqrt(N) or silhouette elbow).
* For logs: cluster by template semantics.
* For tables: treat each table as its own “cluster”; summarization fuses stats.

---

# 7. Retrieval & Scoring (Task Time)

**Steps:**

1. **Task Expansion:** Use LM Studio (fast model) to produce synonyms/facets + modality hints.
2. **Multi-Index Retrieval:**

   * Query each relevant index (text / table / image) with weighting.
3. **MMR Pruning:** Limit similarity redundancy (cosine threshold).
4. **Coverage Balancing:** Ensure each high-level topic (cluster) appears at least once.
5. **Anomaly Guarantee:** Include flagged anomalies/outliers irrespective of lower relevance.

**Scoring Formula (example):**
`Score = α * Relevance + β * Novelty + γ * Importance + δ * AnomalyFlag`
Tune α..δ (start α=0.5, β=0.2, γ=0.2, δ=0.1).

---

# 8. Compression Techniques (Applied Sequentially)

| Order | Technique                           | Effect                                        |
| ----- | ----------------------------------- | --------------------------------------------- |
| 1     | Structural Folding (logs/templates) | Collapse repetitive patterns + counts         |
| 2     | Numeric Aggregation (tables)        | Replace rows with min/mean/max/p95, hist tags |
| 3     | Entity Consolidation                | Group entity roles & frequencies              |
| 4     | Dedup (semantic hash)               | Remove near-identical sentences               |
| 5     | Abstractive Fusion (LM Studio)      | Merge semantically overlapping sets           |
| 6     | Glossary Extraction                 | Move definitions out of main narrative        |
| 7     | Token Tightening Pass               | Compression rewrite to meet hard cap          |

**Outlier Preservation:** Always retain at least 1 raw exemplar bullet for each anomaly type.

---

# 9. Capsule Structure (≤4K Tokens)

| Section                   | Purpose                           | Approx Tokens |
| ------------------------- | --------------------------------- | ------------- |
| Header Instruction & Task | Model guidance + user query       | 150           |
| Global Abstract (L3)      | Cohesive high-level narrative     | 350           |
| Schema & Tables Overview  | Key metrics, distributions        | 350–400       |
| Narrative Key Findings    | Core textual insights             | 700–800       |
| Image / Diagram Summaries | Top K captions + roles            | 250–300       |
| Log / Event Patterns      | Templates + anomalies             | 250–300       |
| Outliers & Anomalies      | Distinct unusual cases            | 250–300       |
| Representative Exemplars  | Raw snippet bullets (multi-modal) | 400–500       |
| Entity Glossary & Roles   | Consolidated entity map           | 250           |
| Topic / Coverage Map      | List of covered themes            | 200           |
| Stubs (Expandable)        | ID → description                  | 200–250       |
| Slack (safety)            | Overflow buffer                   | \~200         |

---

# 10. LM Studio Integration

**API:** OpenAI-compatible `/v1/chat/completions`.

**Provider Abstraction Methods:**

* `chat(messages, temperature, max_tokens, stream)`
* `estimate_tokens(text)`

**Usage Modes:**

| Stage                | Model Size           | Temp |
| -------------------- | -------------------- | ---- |
| Query Expansion      | Fast (7B)            | 0.4  |
| Cluster Fusion (L2)  | 7B / 13B             | 0.2  |
| Global Abstract (L3) | Higher quality (13B) | 0.15 |
| Compression Rewrite  | Fast                 | 0.1  |
| Evaluation QA        | Fast                 | 0.2  |

**Caching:** Key = SHA256(model + concatenated messages). Return cached result if exist.

**Fallbacks:**

1. Timeout → shorten target tokens & retry.
2. Repeated fail → revert to extractive selection.

---

# 11. Provenance & Auditability

* For every bullet, maintain `provenance_chunk_ids` array.
* Inline annotation style (internal use): `[P: c134,c206]`
* UI hover reveals: *File path, page/line numbers*.
* Expansion request uses provenance to reconstruct deeper context.

---

# 12. Stub Expansion Workflow

1. User (or automation) selects `STUB TAB#5`.
2. System fetches underlying cluster/table stats + related raw chunks.
3. Re-run **mini retrieval + compression** limited to that scope (e.g., 1K token delta).
4. Return incremental capsule section (append or replace stub line).

---

# 13. Privacy & PII Redaction

**Detection:** Regex + lightweight NER for: emails, phones, credit cards, IPs, names (optional).
**Redaction Strategy:** Replace with placeholders `[EMAIL_1]`; store reversible map encrypted (SQLCipher).
**Config Toggle:** `pii_redaction: true/false`.
**Image OCR PII:** If high density of digits or email patterns → flag or mask before embedding.

---

# 14. Performance Targets (Mid-Range PC)

| Aspect                                    | Target                             |
| ----------------------------------------- | ---------------------------------- |
| 1M tokens ingestion (text-heavy)          | ≤ 8–10 min (cold)                  |
| Re-build capsule (same dataset, new task) | 20–60 sec                          |
| Memory overhead                           | < 6 GB peak                        |
| Embedding throughput                      | ≥ 1.5K chunks/min (384-dim CPU)    |
| Cluster summarization latency             | < 2.0 s avg per cluster (7B quant) |
| Global abstract                           | < 10 s (13B quant)                 |

**Optimizations:**

* Batch embedding (512–1024 tokens batch).
* Parallel handlers (IO vs CPU separation).
* Reuse canonical chunk hashes to skip unchanged.

---

# 15. Evaluation & Quality Metrics

| Metric             | Method                                          | Threshold/Goal       |
| ------------------ | ----------------------------------------------- | -------------------- |
| Coverage Ratio     | Key entities in capsule / global                | ≥ 0.8                |
| Fidelity (Q\&A)    | Auto Q pairs from original → answer via capsule | ≥ 0.85 accuracy      |
| Redundancy         | Mean cosine similarity of capsule sentences     | < 0.85               |
| Compression Factor | Original tokens / capsule tokens                | ≥ 250×               |
| Modality Balance   | Actual tokens vs quota                          | Within ±10%          |
| Anomaly Retention  | # unique anomaly types retained                 | 100%                 |
| Hallucination Rate | Entities in summaries not in provenance         | 0% (strip offenders) |
| Latency            | Wall clock per capsule                          | Meets targets        |

---

# 16. Configuration (Representative YAML)

```yaml
ingestion:
  max_file_size_mb: 200
  include_extensions: [".pdf",".docx",".txt",".md",".csv",".json",".xlsx",".pptx",".png",".jpg",".log"]
  follow_symlinks: false
  ocr:
    enable: true
    engine: tesseract
    fast_mode_skip_if_pages_over: 1500
  images:
    caption: true
    clip_embeddings: true
    phash_dedupe_distance: 6
    max_images: 500
  tables:
    sample_rows: 5000
    histogram_bins: 16
  logs:
    template_engine: drain
  pii_redaction: true

embeddings:
  text_model: "minilm-384"
  image_model: "clip-vit-b32"
  batch_size: 32

llm:
  provider: lmstudio
  base_url: "http://127.0.0.1:1234/v1"
  models:
    fast: "mistral-7b-instruct"
    quality: "mixtral-8x7b-instruct"   # example
  temps:
    query_expansion: 0.4
    fusion: 0.2
    global_summary: 0.15
    compression: 0.1
  retries: 2
  timeout_seconds: 60

retrieval:
  k_initial: 400
  mmr_lambda: 0.65
  modality_weights:
    text: 0.6
    table: 0.2
    image: 0.2

capsule:
  target_tokens: 4000
  quotas:
    tables: 400
    images: 300
    logs: 300
    exemplars: 500
    glossary: 250
  guaranteed_sections: ["global_abstract","entity_glossary","outliers"]

evaluation:
  qa_pairs: 40
  similarity_threshold: 0.9
```

---

# 17. Development Roadmap (Sprints)

| Sprint | Focus                    | Key Deliverables                                                    |
| ------ | ------------------------ | ------------------------------------------------------------------- |
| 1      | Foundations              | Discovery, hashing, basic text extraction, chunk store, embeddings  |
| 2      | Multi-Modality A         | PDF (text + OCR), DOCX, HTML, basic entity extraction               |
| 2.5    | Multi-Modality B         | Tables (profiling), logs (templates), images (caption + OCR + CLIP) |
| 3      | Clustering & Hierarchies | Multi-modal clustering, L1 extractive, cluster metadata             |
| 4      | LM Studio Integration    | L2 abstractive summaries, caching, failure fallbacks                |
| 5      | Retrieval & Scoring      | Query expansion, multi-index retrieval, MMR, coverage               |
| 6      | Compression Engine       | Aggregation, folding, glossary, token tightening                    |
| 7      | Capsule Assembly & Stubs | 4K builder, provenance mapping, stub framework                      |
| 8      | Expansion & UI           | Interactive CLI or minimal GUI (provenance hover, stub expand)      |
| 9      | Evaluation Harness       | Fidelity tests, metrics logging, tuning knobs                       |
| 10     | Privacy & Optimization   | PII redaction layer, performance profiling, config polish           |
| 11     | Stretch Features         | Differential summary mode, streaming ingestion, multi-model policy  |

---

# 18. Key Algorithms / Pseudocode Sketches

**MMR Retrieval (simplified):**

```python
selected = []
while candidates and len(selected) < budget:
    best = max(candidates, key=lambda c:
               alpha*relevance[c] - (1-alpha)*max_sim(c, selected))
    selected.append(best); candidates.remove(best)
```

**Adaptive Compression Decision:**

```python
if total_tokens(selected_chunks) > soft_cap:
    # escalate abstraction: replace lowest-scoring quartile L0 with their L1 summaries
if still > hard_cap:
    run abstractive fusion across semantically nearest pairs
```

**Hallucination Guard:**

```python
summary_entities = extract_entities(summary_text)
if not summary_entities <= union(entities_from_provenance_chunks):
    remove_or_flag_lines(...)
```

---

# 19. Risk & Mitigation

| Risk                             | Impact            | Mitigation                                             |
| -------------------------------- | ----------------- | ------------------------------------------------------ |
| OCR noise bloats tokens          | Lower fidelity    | Confidence filter + dedup + summarization early        |
| Slow LLM summaries               | Latency spike     | Parallel cluster queue + caching + model tiering       |
| Hallucinations in fusion         | Faithfulness loss | Entity provenance validator + rewrite fallback         |
| Data drift unnoticed             | Stale capsule     | Hash watch + delta detection triggers re-summarize     |
| Token overflow                   | Prompt rejection  | Pre-flight token estimation + compression rewrite pass |
| Large image sets slow captioning | Ingestion delay   | pHash dedupe + cap + lazy caption (on-demand)          |

---

# 20. Stretch & Future Enhancements

| Feature                   | Benefit                                                      |
| ------------------------- | ------------------------------------------------------------ |
| Differential Capsules     | Change tracking between dataset states                       |
| Streaming Mode            | Live logs / folder watcher with rolling capsule              |
| RL Compression Policy     | Learn optimal inclusion patterns per task type               |
| Multi-Model Cascade       | Use faster model for drafts; quality model for final rewrite |
| Active Learning Feedback  | User marks “important” or “irrelevant” to refine scoring     |
| Vector Pruning            | Remove rarely retrieved vectors to shrink footprint          |
| Collaborative Index Merge | Merge multiple folder corpora with conflict resolution       |

---

# 21. Naming & Branding

**Candidates:** *Context Forge*, *CapsuleSmith*, *Distilla*, *TokenLens*, *4KFoundry*.
**Tagline:** “Massive datasets. Focused context. Local. Private.”

---

# 22. Immediate Next Steps (Actionable)

1. **Initialize Repo Skeleton** (`/ingest`, `/modality`, `/summarize`, `/retrieval`, `/compression`, `/capsule`, `/eval`, `/ui`, `/config`).
2. **Implement Sprint 1**:

   * File discovery & hashing
   * Basic TXT / MD / HTML extraction
   * Chunking & embeddings (MiniLM)
   * SQLite schema migrations
3. **Add LM Studio Client Stub** (even if unused yet) so interfaces stay stable.
4. **Basic CLI**:

   * `distilla ingest <folder>`
   * `distilla query "<task>" --capsule out.txt`
5. **Instrument Logging & Timer Metrics** early (baseline performance).

---

# 23. Example Repository Layout

```
context_distiller/
  config/
    default.yaml
  core/
    db.py
    settings.py
    logging.py
  ingest/
    discover.py
    extract_text.py
    extract_pdf.py
    extract_images.py
    extract_tables.py
    ocr.py
  modalities/
    tables.py
    logs.py
    images.py
    code.py
  represent/
    embeddings.py
    clustering.py
    entities.py
    hierarchy.py
  llm/
    provider_base.py
    lmstudio_client.py
    prompts/
       fusion.txt
       global_summary.txt
       compression_rewrite.txt
  retrieval/
    query_expand.py
    multi_index_retrieve.py
    scoring.py
  compression/
    fold_logs.py
    aggregate_tables.py
    fusion.py
    glossary.py
    tighten.py
  capsule/
    assembler.py
    stubs.py
    provenance.py
  eval/
    qa_fidelity.py
    metrics.py
  ui/
    cli.py
  tests/
    ...
  README.md
```

---

# 24. Deliverables You Can Request Next

| Option | Description                                           |
| ------ | ----------------------------------------------------- |
| A      | SQLite DDL script ready to run                        |
| B      | Python skeleton (files with function stubs)           |
| C      | Sample prompt templates (fusion, global, compression) |
| D      | Pseudocode for evaluation harness                     |
| E      | CLI first-run script + config loader                  |

---

**Choose what you want next (A–E or combination), and I’ll produce it.**
If you’d like, I can immediately output the DDL (A) or skeleton (B) to get you coding.

**What’s your pick?** 🚀
