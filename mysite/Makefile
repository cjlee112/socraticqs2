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
	export DJANGO_SETTINGS_MODULE=mysite.settings.test && pytest
	coverage xml
	diff-cover coverage.xml --fail-under=60


quality:
	diff-quality --violations=pycodestyle --fail-under=80 --compare-branch=HEAD~1
	diff-quality --violations=pylint --fail-under=80 --compare-branch=HEAD~1
