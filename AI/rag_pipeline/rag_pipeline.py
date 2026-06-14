#!/usr/bin/env python3
"""
RAG retrieval explorer: query the ChromaDB knowledge base two ways and compare

Author:         Bo Smith (bo@bosmith.tech)
Date:           2026-06-12

Strategy A (baseline):  pure vector similarity search.
Strategy B (reranked):  fetch a wider candidate set by vector similarity, then
                        rescore those candidates with a cross-encoder and keep
                        the best. The cross-encoder reads the query and each
                        chunk together, so it judges relevance far better than
                        the bi-encoder embeddings used for the first pass.

The app shows retrieved chunks and scores rather than a generated answer -- the
point is to make retrieval *quality* visible. Feed the top chunks into an LLM
(see the confluence_ai_agent sample) when you want a written answer.

Dependencies:   A populated Chroma store (run ingest.py first)
                A cross-encoder model (downloaded on first rerank)

Usage:          python rag_pipeline.py
"""
import logging
import os
import gradio as gr
from common import get_arguments, setup_openai, setup_chroma, embed_texts


# Loaded lazily on first rerank. The cross-encoder pulls in sentence-transformers
# (and torch), so we don't pay that import/load cost unless reranking is used.
_RERANKER = None


def get_reranker(model_name: str):
    """
    Load the cross-encoder once and reuse it

    Args:
        model_name  (str)   Cross-encoder model identifier

    Returns:
        reranker    (CrossEncoder)  The loaded model
    """
    global _RERANKER
    if _RERANKER is None:
        from sentence_transformers import CrossEncoder
        logging.info(f"Loading cross-encoder reranker: {model_name}")
        _RERANKER = CrossEncoder(model_name)
    return(_RERANKER)


def vector_search(collection, client, args: dict, query: str, n: int) -> list:
    """
    Embed the query and pull the n nearest chunks by cosine similarity

    Args:
        collection          The Chroma collection
        client      (OpenAI)    AI client
        args        (dict)      Dictionary of arguments
        query       (str)       The user's question
        n           (int)       Number of chunks to retrieve

    Returns:
        hits    (list)  List of {text, source, score} dicts (higher = closer)
    """
    qvec = embed_texts(client, args['embed_model'], [query])[0]
    res = collection.query(query_embeddings=[qvec], n_results=n)
    hits: list = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        # Chroma returns cosine distance; similarity = 1 - distance.
        hits.append({"text": doc, "source": meta["source"], "score": 1 - dist})
    return(hits)


def retrieve_baseline(collection, client, args: dict, query: str) -> list:
    """
    Baseline strategy: return the top_k nearest chunks, as-is.
    """
    return(vector_search(collection, client, args, query, args['top_k']))


def retrieve_reranked(collection, client, args: dict, query: str) -> list:
    """
    Reranked strategy: fetch fetch_k candidates, rescore with the cross-encoder,
    and keep the best top_k.
    """
    candidates = vector_search(
        collection, client, args, query, args['fetch_k'])
    if not candidates:
        return(candidates)
    reranker = get_reranker(args['rerank_model'])
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker.predict(pairs)
    for c, s in zip(candidates, scores):
        c["score"] = float(s)
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return(candidates[:args['top_k']])


def format_hits(hits: list) -> str:
    """
    Render a list of hits as readable markdown blocks
    """
    if not hits:
        return("_No results._")
    blocks: list = []
    for rank, h in enumerate(hits, start=1):
        preview = " ".join(h["text"].split())
        if len(preview) > 300:
            preview = preview[:300] + "…"
        blocks.append(
            f"**{rank}. {h['source']}**  (score: {h['score']:.3f})\n\n{preview}")
    return("\n\n---\n\n".join(blocks))


def main():
    """
    It all starts here. Launch the side-by-side retrieval explorer.
    """
    logging.basicConfig(
        format='%(asctime)s - [%(levelname)-8s] - %(message)s',
        level=logging.DEBUG if os.getenv('DEBUG', None) is not None else logging.INFO,
    )

    args = get_arguments()
    client = setup_openai(args)
    collection = setup_chroma(args)

    if collection.count() == 0:
        logging.warning(
            "Collection is empty -- run `python ingest.py` first.")

    def compare(query: str):
        if not query.strip():
            return("_Enter a question._", "_Enter a question._")
        baseline = format_hits(
            retrieve_baseline(collection, client, args, query))
        reranked = format_hits(
            retrieve_reranked(collection, client, args, query))
        return(baseline, reranked)

    with gr.Blocks(title="RAG Retrieval Explorer") as demo:
        gr.Markdown(
            "# RAG Retrieval Explorer\n"
            "Ask a question and see the same query answered two ways: plain "
            "vector search, and vector search followed by cross-encoder "
            "reranking. Compare which chunks each strategy surfaces.")
        query = gr.Textbox(
            label="Question",
            placeholder="e.g. How do I set up the VPN?")
        btn = gr.Button("Search", variant="primary")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Vector similarity (baseline)")
                out_a = gr.Markdown()
            with gr.Column():
                gr.Markdown("### + Cross-encoder rerank")
                out_b = gr.Markdown()
        btn.click(compare, inputs=query, outputs=[out_a, out_b])
        query.submit(compare, inputs=query, outputs=[out_a, out_b])

    demo.launch()


if __name__ == '__main__':
    main()
