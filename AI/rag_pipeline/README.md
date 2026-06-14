# RAG Pipeline with ChromaDB

A retrieval-augmented generation (RAG) pipeline built on a real vector database.
It ingests a document corpus, chunks and embeds it, stores the vectors in
[ChromaDB](https://www.trychroma.com/), and serves a [Gradio](https://www.gradio.app/)
UI that answers a query two ways — plain vector search and vector search plus
**cross-encoder reranking** — side by side, so the quality difference is visible.

## Why this matters (the plain-English version)

RAG is how you get an AI assistant to answer from *your* documents instead of
from whatever it learned during training. You don't retrain a model — you store
your content in a vector database, and at question time you retrieve the most
relevant passages and hand them to the model. That means answers stay current as
your documents change, and every answer can cite the source it came from.

The catch is that "most relevant" is harder than it sounds, and naive retrieval
often surfaces passages that merely *look* similar to the question. This sample
demonstrates that problem and a proven fix (reranking), with the two approaches
shown next to each other so the improvement is obvious rather than asserted.

## The pipeline

```
 data/*.md ──► chunk ──► embed (API) ──► ChromaDB
                                            │
                                  query ──► embed ──► vector search ──► top-k
                                                            │
                                                      (rerank) cross-encoder ──► better top-k
```

- **Ingestion** (`ingest.py`) — reads the markdown corpus, splits each document
  into overlapping chunks, embeds them through an OpenAI-compatible endpoint,
  and stores them in a persistent ChromaDB collection. Idempotent: re-running
  rebuilds cleanly.
- **Retrieval + UI** (`rag_pipeline.py`) — embeds the question, runs two
  retrieval strategies, and renders the results side by side.
- **Shared config** (`common.py`) — environment parsing, the embeddings call,
  and the Chroma client in one place.

## The two retrieval strategies

| | How it works | Trade-off |
| :-- | :-- | :-- |
| **Baseline** | Embed the query, return the `TOP_K` nearest chunks by cosine similarity. | Fast and cheap, but the embedding model compares query and chunk *separately*, so it can rank loosely-related text too highly. |
| **Reranked** | Fetch a wider `FETCH_K` candidate pool by similarity, then rescore each candidate with a **cross-encoder** that reads the query and chunk *together*, and keep the best `TOP_K`. | A second model pass costs a little latency, but precision improves markedly — the relevant passage tends to jump to the top. |

This is the standard "retrieve wide, rerank narrow" pattern used in production
RAG systems.

## Setup

Run `make setup`, which will:
* Create a Python virtual environment named `.venv`
* Upgrade pip to the latest version
* Install all dependencies from `requirements.txt`

> **Heads-up on size:** the cross-encoder reranker depends on
> `sentence-transformers`, which pulls in PyTorch — the install is a few hundred
> MB. That is the price of a *real* cross-encoder; it runs entirely on-box, and
> the model itself (~80 MB) downloads on first rerank.

Then copy `.env.example` to `.env` and fill in the values:

| Environment Variable | Description |
| :------------------- | :---------- |
| `OPENAI_BASE_URL`    | OpenAI-compatible API base URL, e.g. `https://api.openai.com/v1` |
| `OPENAI_API_KEY`     | API key for the embeddings endpoint |
| `EMBED_MODEL`        | Embedding model, e.g. `text-embedding-3-small` |
| `RERANK_MODEL`       | Cross-encoder model, e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `CHROMA_PATH`        | Where the persistent vector store lives, e.g. `./chroma` |
| `COLLECTION_NAME`    | Chroma collection name, e.g. `knowledge_base` |
| `DATA_DIR`           | Folder of `.md` files to ingest, e.g. `./data` |
| `CHUNK_SIZE`         | Target chunk length in characters, e.g. `800` |
| `CHUNK_OVERLAP`      | Characters carried between adjacent chunks, e.g. `150` |
| `TOP_K`              | Chunks returned to the user, e.g. `5` |
| `FETCH_K`            | Candidates fetched before reranking, e.g. `20` |
| `DEBUG`              | Optional. Set to any value for verbose logging |

## Run

```bash
source .venv/bin/activate

# 1. Build the vector store from data/*.md (only embeddings hit the API)
python ingest.py

# 2. Launch the side-by-side retrieval explorer
python rag_pipeline.py
```

Gradio prints a local URL (e.g. `http://127.0.0.1:7860`). Try questions that the
included knowledge base answers — and especially ones where the wording differs
from the document, which is where reranking earns its keep:

- *"My VPN won't connect, what do I check first?"*
- *"How long do we keep a leaver's email?"*
- *"What do I do if I think an account is hacked?"*

## The sample corpus

`data/` holds a small synthetic MSP/IT knowledge base (VPN setup, password
policy, onboarding, offboarding, backup runbook, incident response). The
documents share vocabulary on purpose — VPN, MFA, accounts, tickets recur across
several — so baseline similarity search has plausible-but-wrong neighbors to
choose from, and reranking has something real to fix. Drop in your own `.md`
files and re-run `ingest.py` to point it at a different corpus.

## Notes

- **Retrieval, not generation, on purpose.** The app shows the *retrieved
  chunks*, not an LLM-written answer. Mixing a generation step in would hide
  which strategy actually retrieved better. To produce a written answer, feed
  the top chunks to a model — the [`confluence_ai_agent`](../confluence_ai_agent)
  sample shows that half.
- **Embeddings via API, reranker local.** Embeddings go through your
  OpenAI-compatible endpoint; the cross-encoder runs on the machine. Swapping
  the endpoint to a local server (vLLM, Ollama) makes the whole pipeline
  on-prem — useful for data-residency requirements.
- **Tuning levers.** `CHUNK_SIZE`/`CHUNK_OVERLAP` change what gets stored;
  `TOP_K`/`FETCH_K` change retrieval breadth. These are the first knobs to turn
  when adapting the pipeline to a real corpus.
