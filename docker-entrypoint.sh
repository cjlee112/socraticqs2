#!/usr/bin/env bash
set -e

case $1 in
	local|dev)
		python manage.py runserver 0.0.0.0:8080 --settings=mysite.settings.docker
		;;
	stage|prod)
		gunicorn --config ../.conf/gunicorn/gunicorn.conf -b :9000 mysite.wsgi
		;;
	migrate)
		python manage.py migrate
		exit 0
		;;
	load-fixtures)
		python manage.py loaddata dumpdata/debug-wo-fsm.json
		exit 0
		;;
	fsm-deploy)
		python manage.py fsm_deploy
		exit 0
		;;
	static)
		python manage.py collectstatic --noinput
		exit 0
		;;
esac

exec "$@"
