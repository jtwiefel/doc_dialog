#!/bin/bash


if [[ $# -eq 0 ]] ; then
    echo 'please provide one argument'
    exit 0
fi

export INSIDE_COMMAND=bash
if [[ $# -eq 2 ]] ; then
    export INSIDE_COMMAND=$2
fi

#docker network create exxxa_euregon_network
#echo docker compose --env-file ../$ENV_PREFIX/debug.env --env-file ../$ENV_PREFIX/hostnames-docker-compose.env --env-file ../$ENV_PREFIX/redis.env --profile $1 build 
#docker compose --env-file ../$ENV_PREFIX/debug.env --env-file ../$ENV_PREFIX/hostnames-docker-compose.env --env-file ../$ENV_PREFIX/redis.env --profile $1 build
#echo docker compose --env-file ../$ENV_PREFIX/debug.env --env-file ../$ENV_PREFIX/hostnames-docker-compose.env --env-file ../$ENV_PREFIX/redis.env --profile $1 up -d
#docker compose --env-file ../$ENV_PREFIX/debug.env --env-file ../$ENV_PREFIX/hostnames-docker-compose.env --env-file ../$ENV_PREFIX/redis.env --profile $1 up -d
#echo compose docker --env-file ../$ENV_PREFIX/debug.env --env-file ../$ENV_PREFIX/hostnames-docker-compose.env --env-file ../$ENV_PREFIX/redis.env  exec $1 $INSIDE_COMMAND
#docker compose --env-file ../$ENV_PREFIX/debug.env --env-file ../$ENV_PREFIX/hostnames-docker-compose.env --env-file ../$ENV_PREFIX/redis.env exec $1 $INSIDE_COMMAND

#docker network create doc_dialog_network
export HOST_HOSTNAME=${HOSTNAME}
export ENTRYPOINT=bash
echo docker compose --profile $1 build 
docker compose --profile $1 build
echo docker compose --profile $1 up -d
docker compose --profile $1 up -d
echo compose docker exec $1 $INSIDE_COMMAND
docker compose exec $1 $INSIDE_COMMAND
