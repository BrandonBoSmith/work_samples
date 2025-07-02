FROM python:3

WORKDIR /opt

COPY ./entrypoint.sh /opt/entrypoint.sh

RUN curl -fsSL https://ollama.com/install.sh | sh

ENTRYPOINT ["/opt/entrypoint.sh"]


