#!/bin/bash
export HOST_HOSTNAME=${HOSTNAME}
export ENTRYPOINT="python doc_dialog/gui.py"
docker compose --profile doc_dialog_llm build
docker compose --profile doc_dialog_llm up