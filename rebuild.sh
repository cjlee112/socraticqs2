#!/usr/bin/env bash
set -e

REGISTRY=local/courselets

ARGS="--build-arg REGISTRY=$REGISTRY --build-arg TAG=base --build-arg STATIC_TAG=static"

prebuild () {
	docker build -t $REGISTRY:static -f Docker/Dockerfile.static .
	docker build -t $REGISTRY:base -f Docker/Dockerfile .
}

build_all () {
	build_dev
	build_test
	build_prod
}

build_dev () {
	docker build -t $REGISTRY/courselets-dev -f Docker/Dockerfile.dev $ARGS .
}

build_test () {
	docker build -t $REGISTRY/courselets-test -f Docker/Dockerfile.test $ARGS .
}

build_prod () {
	docker build --force-rm -t $REGISTRY/courselets -f Docker/Dockerfile.prod $ARGS .
}

case $1 in
	all)
		prebuild
		build_all
	;;
	local|dev)
		prebuild
		build_dev
	;;
	test)
		prebuild
		build_test
	;;
	stage|prod)
		prebuild
		build_prod
	;;
	*)
		echo $"You should specify what to build: $0 {all|local|dev|test|prod}"
	;;
esac
