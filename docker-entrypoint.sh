#!/usr/bin/env bash
set -e

case $1 in
	# sh|bash|make)
	# 	;;
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
	# test)
	# 	apt-get -y update && \
	# 	apt-get install -y \
	# 	make \
	#     python-dev \
	#     gcc \
	#     && rm -rf /var/lib/apt/lists/*
	#     RUN pip install --ignore-installed -U -r /requirements/test.txt
	# local-full|dev-full)
	# 	python manage.py runserver 0.0.0.0:8080 --settings=mysite.settings.docker &
	# 	sleep 5
	# 	python manage.py migrate
	# 	python manage.py loaddata dumpdata/debug-wo-fsm.json
	# 	python manage.py fsm_deploy
		# kill -9 %%
		# sleep 5
		# jobs
		# sleep 5
		# # pkill -f runserver
		# # sleep 10
		# python manage.py runserver 0.0.0.0:8080 --settings=mysite.settings.docker
		# ;;
	# stage-full|prod-full)
	# 	gunicorn --config ../.conf/gunicorn/gunicorn.conf -b :9000 mysite.wsgi
	# 	python manage.py migrate
	# 	python manage.py loaddata dumpdata/debug-wo-fsm.json
	# 	python manage.py fsm_deploy
	# 	;;
	# *)
	# 	echo "Something went wrong"
	# 	echo $"Usage: $0 {blablabla}"
 #        exit 0
		# ;;
esac

exec "$@"
