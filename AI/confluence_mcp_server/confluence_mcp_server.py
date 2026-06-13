#!/usr/bin/env python3
"""
MCP server exposing Atlassian Confluence search as a Model Context Protocol tool

Author:         Bo Smith (bo@bosmith.tech)
Date:           2026-06-12

Dependencies:   Confluence Cloud site + API token
                An MCP-capable client (Claude Desktop, Claude Code, Cursor, ...)

Unlike the companion confluence_ai_agent sample, this server contains no LLM and
no model API key of its own. It speaks the Model Context Protocol over stdio and
advertises a single `search_confluence` tool. The model lives in whichever MCP
client connects to the server; the client decides when to call the tool, and
this server runs the Confluence query and hands back the matching pages.
"""
import logging
import os
import sys
from atlassian import Confluence
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# Logs MUST go to stderr. A stdio MCP server uses stdout for the JSON-RPC wire
# protocol, so anything written to stdout would corrupt the channel and break
# the connection. Python's logging defaults to stderr, which is what we want.
logging.basicConfig(
    format='%(asctime)s - [%(levelname)-8s] - %(message)s',
    level=logging.DEBUG if os.getenv('DEBUG', None) is not None else logging.INFO,
    stream=sys.stderr,
)


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

    # Collect environment variables
    args['conf_url'] = os.getenv('CONFLUENCE_URL', None)
    args['conf_api'] = os.getenv('CONFLUENCE_API_KEY', None)
    args['conf_user'] = os.getenv('CONFLUENCE_USER', None)
    args['search_limit'] = int(os.getenv('SEARCH_LIMIT', '5'))

    # Transport selection. stdio (the default) is launched as a subprocess by a
    # desktop MCP client; streamable-http serves over the network so the server
    # can be hosted once and shared by remote clients. host/port apply only to
    # streamable-http.
    args['transport'] = os.getenv('MCP_TRANSPORT', 'stdio')
    args['host'] = os.getenv('MCP_HOST', '127.0.0.1')
    args['port'] = int(os.getenv('MCP_PORT', '8000'))

    # Check if any required environment variables were not set
    missing: list = [k for k, v in args.items() if v is None]

    # If any of the vars are missing, bail out
    if len(missing) > 0:
        logging.error(f"Arguments not found in environment: {missing}")
        sys.exit(1)

    # Only the transports this server supports. (SSE exists in the SDK but is
    # deprecated in favor of streamable-http, so it is intentionally excluded.)
    valid_transports = ('stdio', 'streamable-http')
    if args['transport'] not in valid_transports:
        logging.error(
            f"Unsupported MCP_TRANSPORT {args['transport']!r}; "
            f"choose one of {valid_transports}")
        sys.exit(1)

    logging.info("Arguments loaded successfully")
    return(args)


def setup_confluence(args: dict) -> Confluence:
    """
    Function to setup the confluence client with the appropriate configurations

    Args:
        args    (dict)  Dictionary of arguments

    Returns:
        confluence  (Confluence)   Confluence client object
    """
    confluence = Confluence(
        url=args['conf_url'],
        username=args['conf_user'],
        password=args['conf_api'],
        cloud=True
    )
    return(confluence)


# Load configuration and the Confluence client once, at import time, so the
# tool below always has them available when the MCP client calls it.
ARGS = get_arguments()
CON = setup_confluence(ARGS)
BASE_URL = ARGS['conf_url'].rstrip("/")

# The MCP server. The name is what shows up in the client's tool/server list.
# host/port are only consulted when running over streamable-http.
mcp = FastMCP("confluence", host=ARGS['host'], port=ARGS['port'])


@mcp.tool()
def search_confluence(query: str) -> str:
    """Search the company Confluence wiki and return the most relevant
    documentation pages, each with a title, a link, and a short summary.

    Call this whenever a question might be answered by internal documentation:
    runbooks, policies, architecture notes, onboarding guides, meeting notes,
    and the like. If the search finds nothing relevant, that is reported back
    plainly rather than guessed at.

    Args:
        query: What to search the wiki for, in natural language.

    Returns:
        Formatted Title / URL / Summary blocks for each matching page, or a
        message indicating that nothing was found or that an error occurred.
    """
    cql = f'siteSearch ~ "{query}" AND type = page'
    try:
        response = CON.cql(cql, limit=ARGS['search_limit'])
    except Exception as err:
        logging.error("An error occurred searching confluence")
        logging.error(str(err))
        return(f"Error searching Confluence: {err}")

    hits = response.get("results", [])
    if not hits:
        return(f'No Confluence pages found for "{query}".')

    blocks: list = []
    for hit in hits:
        content = hit.get("content", {})
        title = content.get("title", "Untitled")
        webui = content.get("_links", {}).get("webui", "")
        url = f"{BASE_URL}{webui}" if webui else BASE_URL
        # The CQL excerpt is a short snippet of the page; Confluence wraps the
        # matched terms in @@@hl@@@ markers, so strip those for readability.
        summary = hit.get("excerpt", "").replace("@@@hl@@@", "").replace(
            "@@@endhl@@@", "").strip()
        blocks.append(f"Title: {title}\nURL: {url}\nSummary: {summary}")

    logging.info(f"search_confluence returned {len(blocks)} page(s)")
    return("\n\n---\n\n".join(blocks))


def main():
    """
    It all starts here. Serve the MCP server on the configured transport.

    stdio (the default) is launched as a subprocess by a desktop MCP client
    (Claude Desktop, Claude Code, Cursor, ...). streamable-http serves over the
    network so the server can be hosted once and shared by remote clients --
    run that behind your own authentication.
    """
    transport = ARGS['transport']
    if transport == 'streamable-http':
        logging.info(
            f"Starting Confluence MCP server on "
            f"http://{ARGS['host']}:{ARGS['port']}"
            f"{mcp.settings.streamable_http_path}")
    else:
        logging.info("Starting Confluence MCP server on stdio")
    mcp.run(transport=transport)


if __name__ == '__main__':
    main()
