
# make debug dumpdata for devs
debugdump:
	python manage.py dumpdata >dumpdata/debug.json
	python manage.py dumpdata -e contenttypes >dumpdata/debug-e.json

# backup production database
backup:
	cp mysite.db dumpdata/mysite.db.production
	python manage.py dumpdata >dumpdata/production.json
	python manage.py dumpdata -e contenttypes >dumpdata/production-e.json
