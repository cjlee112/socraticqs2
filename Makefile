env :=

LOCAL_ENV := local
DEV_ENV := dev
STAGE_ENV := stage
PROD_ENV := prod

NGINX_HOST = localhost
NGINX_PORT = 8080
DOCKER_REGISTRY = registry-gitlab.raccoongang.com/cmltawt0/socraticqs2

GIT_TAG := $(shell git describe --abbrev=0)
VERSION :=

DEFAULT_APP_PWD = mysite/mysite
# server APP_PWD for prod: /courselets/app
# server DEV_APP_PWD for dev: /courselets/dev/app

ifneq ($(filter $(env),$(STAGE_ENV) $(PROD_ENV)),)
	DOCKERFILE_PATH := Docker/Dockerfile.prod
	DOCKERCOMPOSE_PATH := prod.yml
	APP = app
	export NGINX_HOST
	export NGINX_PORT
else ifneq ($(filter $(env),$(DEV_ENV)),)
	DOCKERFILE_PATH := Docker/Dockerfile.dev
	DOCKERCOMPOSE_PATH := dev.yml
	APP = dev_app
else
	DOCKERFILE_PATH := Docker/Dockerfile.dev
	DOCKERCOMPOSE_PATH := docker-compose.yml
	APP = local_app
endif

sh:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) bash

run:
	docker-compose -f $(DOCKERCOMPOSE_PATH) up -d

start:
	docker-compose -f $(DOCKERCOMPOSE_PATH) start

restart:
	docker-compose -f $(DOCKERCOMPOSE_PATH) restart

debug:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run --service-ports $(APP)

build: .prebuild .build .touch .migrate .load-fixtures .fsm-deploy
ifneq ($(filter $(env),$(STAGE_ENV) $(PROD_ENV)),)
	make .static
endif
ifneq ($(filter $(env),$(LOCAL_ENV)),)
	make .react
endif

.prebuild:
	docker build --build-arg node_env=production -t local/courselets:static-local -f Docker/Dockerfile.static .
	docker build -t local/courselets:base-local -f Docker/Dockerfile .

.build:
	docker-compose -f $(DOCKERCOMPOSE_PATH) build

.touch:
	touch $(DEFAULT_APP_PWD)/settings/local.py

.migrate:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) \
			python manage.py migrate

.fsm-deploy:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) \
			python manage.py fsm_deploy

.load-fixtures:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) \
			python manage.py loaddata dumpdata/debug-wo-fsm.json

.init-data:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) \
			python manage.py flush

	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) \
			python manage.py loaddata dumpdata/debug-wo-fsm.json

.static:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run --no-deps $(APP) \
			python manage.py collectstatic --noinput

.react:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run react

.prepare-geo:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run --no-deps $(APP) \
			bash -c \
			" \
			find . | grep -E "GeoLiteCity.dat.gz" | xargs rm -rf && \
			wget -q http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz && \
			gunzip GeoLiteCity.dat.gz && \
			mv GeoLiteCity.dat GeoLiteCityLocal.dat \
			"

stop:
	docker-compose -f $(DOCKERCOMPOSE_PATH) stop

rm:
	docker-compose -f $(DOCKERCOMPOSE_PATH) rm

test:
	docker-compose -f $(DOCKERCOMPOSE_PATH) run $(APP) \
			bash -c \
			" \
			find . | grep -E \"(__pycache__|\.pyc|\.pyo$\)\" | xargs rm -rf && \
			make coverage \
			"

version:
	echo "Tagged release $(VERSION)\n" > Changelog-$(VERSION).txt
	git log --oneline --no-decorate --no-merges $(GIT_TAG)..HEAD >> Changelog-$(VERSION).txt
	git tag -s -F Changelog-$(VERSION).txt $(VERSION)
