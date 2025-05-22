# Papermill
`papermill` is planned to be an AI‑powered knowledge explorer designed to turn an unstructured library of research papers, e‑books, lecture notes, and internal documents into an interactive, searchable knowledge graph. It couples a modern Retrieval‑Augmented Generation (RAG) pipeline with concept‑mapping and summarization agents so that users can use natural‑language queries to retrieve and summarize documents while enabling similar concept mapping.

## Key Features (planned)

- Automated ETL & Embedding – Stream documents of any common format (PDF, EPUB, Markdown, HTML, slides, misc text formats, etc) through an ETL pipeline, generate embeddings with OpenAI/Instructor or some other LLM, and store them in Qdrant. Metadata is auto‑extracted and normalized with a rule-based system.

- Semantic & Hybrid Search – Combine k‑NN vector search with traditional keyword and metadata filters for high‑recall retrieval.

- Hierarchical Summarization – On‑the‑fly abstractive summaries of documents or collections, with citations.

- Concept Mapping – Build and display graphs of related concepts, authors, and topics powered by embedding similarity plus LLM relation extraction.

- Advanced Query Language – Allow power users to craft structured queries (e.g., similar_to:, published_after:) via a simple DSL.

- Agentic Format‑Handlers – Small specialized agents parse edge‑case formats (scanned PDFs, code notebooks, etc.).

- Observability Dashboard – Live metrics on latency, token/GPU usage, Qdrant health, and accuracy feedback loops.

- CI/CD & DevOps Ready – GitHub Actions, Docker‑Compose/K8s deployments, and an integration‑test harness with synthetic questions.


## Tentative Roadmap

|Milestone|Core Deliverables|
|---|---|
|**M0 – Scaffold & POC**|Repo skeleton, Docker env, basic ETL -> Qdrant ingestion, simple retrieval API|
|**M1 – Core RAG API**|Retrieval with Haystack or similar, summarizer integration, streaming answer endpoints|
|**M2 – Concept Mapper & UI**|React/Next.js UI, graph visualization, relevance‑feedback collection|
|**M3 – Observability & CI/CD**|Prometheus/Grafana stack, GitHub Actions pipelines, chaos tests|
|**M4 – Scale & Multi‑tenant access**|Horizontal sharding, role‑based auth|



## Installation

using rye

```sh
rye install --dev
```

using the requirements file directly, e.g.
```sh
pip install -r requirements.lock
```

> [!WARNING] changes to `requirements.lock`
> Certain Linux-specific Python libraries have been commented out of the requirements.lock until proper containerization is added.


> [!NOTE] CUDA-enabled `torch` versions
> For CUDA-enabled Pytorch installations, you should [install from wheel.](https://pytorch.org/get-started/locally/)