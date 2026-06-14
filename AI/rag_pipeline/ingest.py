#!/usr/bin/env python3
"""
Ingestion pipeline for the RAG sample

Author:         Bo Smith (bo@bosmith.tech)
Date:           2026-06-12

Loads every markdown file under DATA_DIR, splits each into overlapping chunks,
embeds the chunks via an OpenAI-compatible endpoint, and stores them in
ChromaDB. Re-running clears the collection first, so it's idempotent.

Usage:          python ingest.py
"""
import glob
import logging
import os
from common import get_arguments, setup_openai, setup_chroma, embed_texts


def split_paragraph(paragraph: str, chunk_size: int) -> list:
    """
    Split a single oversized paragraph into word-bounded pieces <= chunk_size

    Most paragraphs are smaller than a chunk and pass through untouched; this
    only fires for the occasional paragraph that is longer than chunk_size on
    its own, so that no chunk silently exceeds the configured size.

    Args:
        paragraph   (str)   A single paragraph
        chunk_size  (int)   Maximum piece length in characters

    Returns:
        pieces  (list)  One or more pieces, each at most chunk_size characters
    """
    pieces: list = []
    current = ""
    for word in paragraph.split():
        if current and len(current) + 1 + len(word) > chunk_size:
            pieces.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        pieces.append(current)
    return(pieces)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list:
    """
    Split text into overlapping chunks on paragraph boundaries

    Paragraphs (blank-line separated) are packed into chunks up to chunk_size
    characters. A paragraph longer than chunk_size is first broken into
    word-bounded pieces so no chunk exceeds the limit. When a chunk is closed,
    the trailing `overlap` characters are carried into the next one so context
    isn't lost at the seams -- chunking is the single most impactful knob for
    retrieval quality.

    Args:
        text        (str)   The full document text
        chunk_size  (int)   Maximum chunk length in characters
        overlap     (int)   Characters carried from the end of one chunk to
                            the start of the next

    Returns:
        chunks  (list)  List of chunk strings
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Explode any paragraph that is larger than a whole chunk, so the packing
    # loop below only ever deals with units that fit.
    units: list = []
    for para in paragraphs:
        if len(para) > chunk_size:
            units.extend(split_paragraph(para, chunk_size))
        else:
            units.append(para)

    chunks: list = []
    current = ""
    for unit in units:
        if current and len(current) + len(unit) + 2 > chunk_size:
            chunks.append(current.strip())
            # Carry overlap from the tail of the chunk we just closed.
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{unit}" if tail else unit
        else:
            current = f"{current}\n\n{unit}" if current else unit
    if current.strip():
        chunks.append(current.strip())
    return(chunks)


def load_documents(data_dir: str) -> list:
    """
    Read every .md file under data_dir

    Args:
        data_dir    (str)   Directory holding the corpus

    Returns:
        docs    (list)  List of (source_filename, text) tuples
    """
    docs: list = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(path, "r", encoding="utf-8") as fh:
            docs.append((os.path.basename(path), fh.read()))
    return(docs)


def main():
    """
    It all starts here. Build (or rebuild) the vector store from the corpus.
    """
    logging.basicConfig(
        format='%(asctime)s - [%(levelname)-8s] - %(message)s',
        level=logging.DEBUG if os.getenv('DEBUG', None) is not None else logging.INFO,
    )

    args = get_arguments()
    client = setup_openai(args)
    collection = setup_chroma(args)

    # Start clean so re-running ingest doesn't pile up duplicate chunks.
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        logging.info(f"Cleared {len(existing['ids'])} existing chunk(s)")

    docs = load_documents(args['data_dir'])
    if not docs:
        logging.error(f"No .md files found in {args['data_dir']}")
        return

    ids: list = []
    documents: list = []
    metadatas: list = []
    for source, text in docs:
        chunks = chunk_text(text, args['chunk_size'], args['chunk_overlap'])
        for i, chunk in enumerate(chunks):
            ids.append(f"{source}::{i}")
            documents.append(chunk)
            metadatas.append({"source": source, "chunk": i})
        logging.info(f"{source}: {len(chunks)} chunk(s)")

    logging.info(
        f"Embedding {len(documents)} chunk(s) via {args['embed_model']}")
    embeddings = embed_texts(client, args['embed_model'], documents)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logging.info(
        f"Stored {len(ids)} chunk(s) in collection '{args['collection']}'")


if __name__ == '__main__':
    main()
