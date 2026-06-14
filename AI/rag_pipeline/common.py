#!/usr/bin/env python3
"""
Shared configuration and helpers for the RAG pipeline sample

Author:         Bo Smith (bo@bosmith.tech)
Date:           2026-06-12

Dependencies:   ChromaDB (persistent vector store)
                An OpenAI-compatible embeddings endpoint

Both ingest.py and rag_pipeline.py import from here so the config, the Chroma
client, and the embedding call are defined in exactly one place.
"""
import logging
import os
import sys
import chromadb
from dotenv import load_dotenv
from openai import OpenAI


def get_arguments() -> dict:
    """
    Function to parse environment variables safely

    Returns:
        args    (dict)  Dictionary of argument variables
    """
    args: dict = {}
    logging.info("Getting environment variables from .env file")
    try:
        load_dotenv(override=True)
    except Exception:
        logging.info(
            "Unable to get variables from .env, looking at environment"
        )

    # OpenAI-compatible embeddings endpoint
    args['openai_base_url'] = os.getenv('OPENAI_BASE_URL', None)
    args['openai_api_key'] = os.getenv('OPENAI_API_KEY', None)
    args['embed_model'] = os.getenv('EMBED_MODEL', None)

    # Cross-encoder reranker (downloaded locally on first use)
    args['rerank_model'] = os.getenv(
        'RERANK_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')

    # Vector store + corpus
    args['chroma_path'] = os.getenv('CHROMA_PATH', './chroma')
    args['collection'] = os.getenv('COLLECTION_NAME', 'knowledge_base')
    args['data_dir'] = os.getenv('DATA_DIR', './data')

    # Chunking + retrieval knobs
    args['chunk_size'] = int(os.getenv('CHUNK_SIZE', '800'))
    args['chunk_overlap'] = int(os.getenv('CHUNK_OVERLAP', '150'))
    args['top_k'] = int(os.getenv('TOP_K', '5'))
    args['fetch_k'] = int(os.getenv('FETCH_K', '20'))

    # Only these three are required; the rest have sensible defaults.
    required = ['openai_api_key', 'embed_model']
    missing: list = [k for k in required if args[k] is None]
    if len(missing) > 0:
        logging.error(f"Arguments not found in environment: {missing}")
        sys.exit(1)

    logging.info("Arguments loaded successfully")
    return(args)


def setup_openai(args: dict) -> OpenAI:
    """
    Function to setup the OpenAI-compatible client

    Args:
        args    (dict)  Dictionary of arguments

    Returns:
        client  (OpenAI)    OpenAI client object
    """
    if args['openai_base_url'] is not None:
        logging.info(f"Using OpenAI-compatible endpoint at {args['openai_base_url']}")
        client = OpenAI(
            base_url=args['openai_base_url'],
            api_key=args['openai_api_key'],
        )
    else:
        logging.info("Using OpenAI's official API endpoint")
        client = OpenAI(
            api_key=args['openai_api_key'],
        )
    return(client)


def setup_chroma(args: dict):
    """
    Function to open the persistent Chroma store and get/create the collection

    Args:
        args    (dict)  Dictionary of arguments

    Returns:
        collection  (chromadb Collection)   The knowledge-base collection
    """
    client = chromadb.PersistentClient(path=args['chroma_path'])
    # cosine space matches how embeddings are typically compared; the default
    # is l2, so set it explicitly to keep similarity scores intuitive.
    collection = client.get_or_create_collection(
        name=args['collection'],
        metadata={"hnsw:space": "cosine"},
    )
    return(collection)


def embed_texts(client: OpenAI, model: str, texts: list) -> list:
    """
    Embed a batch of texts via the OpenAI-compatible embeddings endpoint

    Args:
        client  (OpenAI)    AI client
        model   (str)       Embedding model name
        texts   (list)      List of strings to embed

    Returns:
        vectors (list)  One embedding vector (list of floats) per input text,
                        in the same order as the input.
    """
    response = client.embeddings.create(model=model, input=texts)
    # The API returns items in input order, but sort by index defensively.
    items = sorted(response.data, key=lambda d: d.index)
    return([item.embedding for item in items])
