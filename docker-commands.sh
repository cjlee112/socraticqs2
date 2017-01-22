#!/usr/bin/env sh

echo "Clearing .pyc files."
find /code/ -name "*.pyc" -delete
echo "Done."


echo "Starting development server."
python2.7 manage.py runserver 0.0.0.0:8000 --settings=mysite.settings.docker
