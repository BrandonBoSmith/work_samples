#!/usr/bin/env python3
"""
Sample AI agent which retrieves knowledge from a Atlassian Conflucence site

Author:         Bo Smith (bo@bosmith.tech)
Date:           2026-02-04

Dependencies:   Confluence Cloud site
                API key for an OpenAI compatible AI inference platform
"""
import logging
import gradio as gr
import os
import pprint
import sys
from atlassian import Confluence
from dotenv import load_dotenv
from openai import OpenAI


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
    args['ai_url'] = os.getenv('AI_BASE_URL', None)
    args['ai_key'] = os.getenv('AI_API_KEY', None)

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
    openai = OpenAI(
        base_url=os.getenv(args['ai_url']),
        api_key=os.getenv(args['ai_key'])
    )
    return(openai)


def search_confluence(args: dict) -> str:
    """
    Function to search confluence
    # TODO add search parameter provided through gradio
    Args:
        args    (dict)  Dictionary of variables

    Returns:
        results (string)    Confluence search results
    """
    con = Confluence(
        url=args['conf_url'],
        username=args['conf_user'],
        password=args['conf_api'],
        cloud=True
    )

    search = "python"
    cql = f'siteSearch ~ "{search}" AND type = page'
    try:
        results = con.cql(cql, limit=100)
        return(results)
    except Exception as err:
        logging.error("An error occurred searching confluence")
        logging.error(str(err))
        return(str(err))


def main():
    """
    It all starts here
    """
    # Setup Logging.  Whutcha doin under there?
    if os.getenv('DEBUG', None) != None:
        logging.basicConfig(
            format='%(asctime)s - [%(levelname)-8s] - %(message)s',
            level=logging.DEBUG
        )
    # Ne'er mind, I don't care ;)
    else:
        logging.basicConfig(
            format='%(asctime)s - [%(levelname)-8s] - %(message)s',
            level=logging.DEBUG
        )

    # Give me the arguments, but don't argue with me.
    args = get_arguments()
    # Come hither my digital minion! 
    # openai = setup_openai(args)
    results = search_confluence(args)


if __name__ == '__main__':
    main()