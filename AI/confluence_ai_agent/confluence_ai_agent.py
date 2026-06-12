#!/usr/bin/env python3
"""
Sample AI agent which retrieves knowledge from a Atlassian Conflucence site

Author:         Bo Smith (bo@bosmith.tech)
Date:           2026-02-04

Dependencies:   Confluence Cloud site
                API key for an OpenAI compatible AI inference platform
                (the model must support function/tool calling)
"""
import json
import logging
import gradio as gr
import os
import pprint
import sys
from atlassian import Confluence
from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using the company's "
    "Confluence wiki. When a question may be answered by internal "
    "documentation, call the search_confluence tool to look it up. For each "
    "relevant page, reply with a link to the page and a short summary of its "
    "contents. If the search returns nothing relevant, say you couldn't find "
    "it in Confluence rather than guessing."
)

# Tool schema advertised to the model.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_confluence",
            "description": (
                "Search the company Confluence wiki and return the most "
                "relevant documentation pages, each with a link and a short "
                "summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search the wiki for.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


def get_arguments():
    """
    Function to parse environment variables safely

    Returns:
        args    (dict)  Dictionary of argument variables
    """
    args: dict = {}
    logging.info("Getting environment variables from .env file")
    try:
        load_dotenv(override=True)
    except:
        logging.info(
            "Unable to get variables from .env, looking at environment"
        )

    # Collect environment variables
    args['conf_url'] = os.getenv('CONFLUENCE_URL', None)
    args['conf_api'] = os.getenv('CONFLUENCE_API_KEY', None)
    args['conf_user'] = os.getenv('CONFLUENCE_USER', None)
    args['search_limit'] = int(os.getenv('SEARCH_LIMIT', '5'))
    args['max_agent_steps'] = int(os.getenv('MAX_AGENT_STEPS', '5'))
    args['ai_model'] = os.getenv('MODEL', None)

    # Check if any environment variables were not set
    missing: list = [k for k, v in args.items() if v == None]

    # If any of the vars are missing, bail out
    if len(missing) > 0:
        logging.error(
            f"Arguments not found in environment: {pprint.pformat(missing)}")
        sys.exit(1)
    else:
        logging.info("Arguments loaded successfully")
        logging.debug("Arguments")
        logging.debug(pprint.pformat(args))

    return(args)


def setup_openai(args: dict) -> OpenAI:
    """
    Function to setup the openai client with the appropriate configurations

    Args:
        args    (dict)  Dictionary of arguments

    Returns:
        openai  (OpenAI)    OpenAI client object
    """
    # Create an OpenAI client configured by environment variables.
    openai = OpenAI()
    return(openai)


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


def search_confluence(args: dict, query: str, con: Confluence) -> str:
    """
    Function to search confluence and return a link and summary per page

    Args:
        args    (dict)          Dictionary of variables (used for base URL)
        query   (str)           Search terms supplied by the model
        con     (Confluence)    Confluence client

    Returns:
        results (string)    Formatted Title / URL / summary blocks, or an
                            error / "no results" message.
    """
    cql = f'siteSearch ~ "{query}" AND type = page'
    try:
        response = con.cql(
            cql,
            limit=args["search_limit"]
        )
    except Exception as err:
        logging.error("An error occurred searching confluence")
        logging.error(str(err))
        return(f"Error searching Confluence: {err}")

    hits = response.get("results", [])
    if not hits:
        return(f'No Confluence pages found for "{query}".')

    base = args['conf_url'].rstrip("/")
    blocks: list = []
    for hit in hits:
        content = hit.get("content", {})
        title = content.get("title", "Untitled")
        webui = content.get("_links", {}).get("webui", "")
        url = f"{base}{webui}" if webui else base
        # The CQL excerpt is a short snippet of the page; Confluence wraps the
        # matched terms in @@@hl@@@ markers, so strip those for readability.
        summary = hit.get("excerpt", "").replace("@@@hl@@@", "").replace(
            "@@@endhl@@@", "").strip()
        blocks.append(f"Title: {title}\nURL: {url}\nSummary: {summary}")

    logging.debug(f"search_confluence returned {len(blocks)} page(s)")
    return("\n\n---\n\n".join(blocks))


def run_agent(client: OpenAI, con: Confluence, args: dict,
              messages: list) -> str:
    """
    Drive the tool-calling loop: let the model decide when to search
    Confluence, feed results back, and return its final answer.

    Args:
        client      (OpenAI)        AI client
        con         (Confluence)    Confluence client
        args        (dict)          Dictionary of arguments
        messages    (list)          Conversation so far (mutated in place)

    Returns:
        answer  (str)   The assistant's final text response.
    """
    for _ in range(args["max_agent_steps"]):
        response = client.chat.completions.create(
            model=args['ai_model'],
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        # No tool calls -> the model produced its final answer.
        if not message.tool_calls:
            return(message.content or "")

        # Record the assistant turn (with its tool calls) before answering.
        messages.append(message)
        for tool_call in message.tool_calls:
            query = json.loads(tool_call.function.arguments).get("query", "")
            logging.info(f"Tool call: search_confluence(query={query!r})")
            result = search_confluence(args, query, con)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    logging.warning("Agent hit the tool-call step limit")
    return("I wasn't able to find a confident answer in Confluence within "
           "the allowed number of lookups.")


def main():
    """
    It all starts here
    """
    # Setup Logging.  Whutcha doin under there?  DEBUG if asked, else INFO.
    level = logging.DEBUG if os.getenv('DEBUG', None) != None else logging.INFO
    logging.basicConfig(
        format='%(asctime)s - [%(levelname)-8s] - %(message)s',
        level=level
    )

    # Give me the arguments, but don't argue with me.
    args = get_arguments()
    con = setup_confluence(args)

    # Come hither my digital minions!
    client = setup_openai(args)

    def respond(message: str, history: list) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        return(run_agent(client, con, args, messages))

    gr.ChatInterface(
        fn=respond,
        title="Confluence Agent",
        description="Ask a question and I'll look it up in Confluence.",
    ).launch()


if __name__ == '__main__':
    main()
