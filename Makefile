env :=

LOCAL_ENV := local
DEV_ENV := dev
STAGE_ENV := stage
PROD_ENV := prod

NGINX_HOST = localhost
NGINX_PORT = 8080

GIT_TAG := $(shell git describe --abbrev=0)
VERSION :=


ifneq ($(filter $(env),$(STAGE_ENV) $(PROD_ENV)),)
	DOCKERFILE_PATH := prod.yml
	APP = app
	export NGINX_HOST
	export NGINX_PORT
endif

ifneq ($(filter $(env),$(DEV_ENV)),)
	DOCKERFILE_PATH := dev.yml
	APP = dev_app
else
	DOCKERFILE_PATH := docker-compose.yml
	APP = local_app
endif


sh:
	docker-compose -f $(DOCKERFILE_PATH) run $(APP) bash

run:
	docker-compose -f $(DOCKERFILE_PATH) up -d

start:
	docker-compose -f $(DOCKERFILE_PATH) start

restart:
	docker-compose -f $(DOCKERFILE_PATH) restart

debug:
	docker-compose -f $(DOCKERFILE_PATH) run --service-ports $(APP)

build: .build .migrate .load-fixtures .fsm-deploy
ifneq ($(filter $(env),$(STAGE_ENV) $(PROD_ENV)),)
	make .static
endif
ifneq ($(filter $(env),$(LOCAL_ENV)),)
	make .react
endif

.build:
	docker-compose -f $(DOCKERFILE_PATH) build

.migrate:
	docker-compose -f $(DOCKERFILE_PATH) run $(APP) \
			python manage.py migrate

.fsm-deploy:
	docker-compose -f $(DOCKERFILE_PATH) run $(APP) \
			python manage.py fsm_deploy

.load-fixtures:
	docker-compose -f $(DOCKERFILE_PATH) run $(APP) \
			python manage.py loaddata dumpdata/debug-wo-fsm.json

.init-data:
	docker-compose -f $(DOCKERFILE_PATH) run $(APP) \
			python manage.py flush

	docker-compose -f $(DOCKERFILE_PATH) run $(APP) \
			python manage.py loaddata dumpdata/debug-wo-fsm.json

.static:
	docker-compose -f $(DOCKERFILE_PATH) run --no-deps $(APP) \
			python manage.py collectstatic --noinput

.react:
	docker-compose -f $(DOCKERFILE_PATH) run react

.prepare-geo:
	docker-compose -f $(DOCKERFILE_PATH) run --no-deps $(APP) \
			bash -c \
			" \
			find . | grep -E "GeoLiteCity.dat.gz" | xargs rm -rf && \
			wget -q http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz && \
			gunzip GeoLiteCity.dat.gz && \
			mv GeoLiteCity.dat GeoLiteCityLocal.dat \
			"

stop:
	docker-compose -f $(DOCKERFILE_PATH) stop

rm:
	docker-compose -f $(DOCKERFILE_PATH) rm

test:
	docker-compose -f $(DOCKERFILE_PATH) run $(APP) \
			bash -c \
			" \
			find . | grep -E \"(__pycache__|\.pyc|\.pyo$\)\" | xargs rm -rf && \
			make coverage \
			"

version:
	echo "Tagged release $(VERSION)\n" > Changelog-$(VERSION).txt
	git log --oneline --no-decorate --no-merges $(GIT_TAG)..HEAD >> Changelog-$(VERSION).txt
	git tag -s -F Changelog-$(VERSION).txt $(VERSION)
