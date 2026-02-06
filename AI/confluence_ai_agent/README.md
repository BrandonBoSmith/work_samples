# Confluence Agent
This agent is configured with a "tool" that will integrate with Confluence to restrieve appropriate knowledge articles.  Typically this would be done through an MCP server, but I thought it would be fun to have an agent that was directly integrated.

## Setup
Run `make setup` which will perform the following
* Create a python virtual environment named `.venv`
* Upgrade pip to the latest version
* Install all necessary dependencies
Once this is done, create an `.env` file with the following environment variables

| Environment Variable | Description |
| :------------------- | :---------- |
| CONFLUENCE_URL | The URL to your Confluence Instance |
| CONFLUENCE_API_KEY | API key to your Convludence Insance |
| AI_URL | AI API URL e.g. "https://ollama.com/v1" |
| AI_API_KEY | API Key for your AI |
