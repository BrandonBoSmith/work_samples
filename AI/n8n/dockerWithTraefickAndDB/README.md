# n8n Docker Compose
This is my version of a functional docker-compose with the following features
* Postgres Database
* Traefik reverse proxy
* Let's Encrypt Certificate
* Environment Variable settings to ensure proper webhook URL path with reverse proxy
* * Variables set in .env file
* Docker Volumes
* * Postgres
* * Traefik
* * n8n

## Deploy
```
docker compose up -d
```
