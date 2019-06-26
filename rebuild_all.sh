#!/usr/bin/env bash
REGISTRY=local/courselets
TAG=local

docker build -t $REGISTRY:static -f Docker/Dockerfile.static .
docker build -t $REGISTRY:base -f Docker/Dockerfile .

docker build --force-rm -t $REGISTRY:courselets -f Docker/Dockerfile.prod --build-arg REGISTRY=$REGISTRY --build-arg TAG=base --build-arg STATIC_TAG=static .

docker build -t $REGISTRY:courselets-test -f Docker/Dockerfile.test --build-arg REGISTRY=$REGISTRY --build-arg TAG=base --build-arg STATIC_TAG=static .

docker build -t $REGISTRY:courselets-dev -f Docker/Dockerfile.dev --build-arg REGISTRY=$REGISTRY --build-arg TAG=base --build-arg STATIC_TAG=static .
