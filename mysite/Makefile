test:
	pytest

# make debug dumpdata for devs
debugdump:
	python manage.py dumpdata >dumpdata/debug.json
	python manage.py dumpdata -e contenttypes >dumpdata/debug-e.json

# backup production database
backup:
	cp mysite.db dumpdata/mysite.db.production
	python manage.py dumpdata >dumpdata/production.json
	python manage.py dumpdata -e contenttypes >dumpdata/production-e.json

coverage:
	export DJANGO_SETTINGS_MODULE=mysite.settings.test && pytest -n 4
	coverage xml
# 	diff-cover coverage.xml --fail-under=60


quality:
	echo "TODO: fix this and find out how to use with gitlab"
# 	diff-quality --violations=pycodestyle --fail-under=80 --compare-branch=HEAD~1
# 	diff-quality --violations=pylint --fail-under=80 --compare-branch=HEAD~1

run:
	python manage.py runserver 0.0.0.0:8000 --settings=mysite.settings.docker