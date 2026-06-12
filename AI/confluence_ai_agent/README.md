# Confluence Agent

An AI agent that answers questions from your Atlassian Confluence wiki. The agent is given a
`search_confluence` **tool**; the model decides when to search, gets back a link and short
summary for each matching page, and replies with those citations. Typically this kind of
integration is done through an MCP server, but I thought it would be fun to have an agent that
was directly integrated.

A [Gradio](https://www.gradio.app/) chat UI is provided so you can talk to it in the browser.

## Setup

Run `make setup`, which will:
* Create a Python virtual environment named `.venv`
* Upgrade pip to the latest version
* Install all dependencies from `requirements.txt`

Then copy `.env.example` to `.env` and fill in the values:

| Environment Variable | Description |
| :------------------- | :---------- |
| `CONFLUENCE_URL`     | URL to your Confluence instance, e.g. `https://your-site.atlassian.net/wiki` |
| `CONFLUENCE_USER`    | Email of the Confluence account the API token belongs to |
| `CONFLUENCE_API_KEY` | Confluence API token |
| `SEARCH_LIMIT`       | Max Confluence pages returned per search, e.g. `5` |
| `OPENAI_BASE_URL`    | OpenAI-compatible API base URL, e.g. `https://api.openai.com/v1` |
| `OPENAI_API_KEY`     | API key for the AI endpoint |
| `MODEL`              | Model name to use, e.g. `gpt-4o-mini` (must support tool calling) |
| `MAX_AGENT_STEPS`    | Max tool-call round trips before the agent gives up, e.g. `5` |
| `DEBUG`              | Optional. Set to any value for verbose logging (shows tool calls) |

> **Note:** the AI endpoint must support OpenAI function/tool calling.

## Run

```bash
source .venv/bin/activate
python confluence_ai_agent.py
```

Gradio prints a local URL (e.g. `http://127.0.0.1:7860`). Open it and ask a question; the agent
searches Confluence and answers with links and summaries of the relevant pages.
