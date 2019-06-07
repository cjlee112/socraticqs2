#!/bin/sh

name='mongo'

[[ $(docker ps -f "name=$name" --format '{{.Names}}') == $name ]] ||
docker run -d --name mongo -p 27017:27017 mongo:latest