#!/bin/sh

name='mongo'

[[ $(docker ps -f "name=$name" --format '{{.Names}}') == $name ]] ||
docker stop mongo
