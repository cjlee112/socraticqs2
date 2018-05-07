#!/usr/bin/env sh

echo "Installing requirements..."
pip install -r ../requirements.txt

echo "Running migrations...."
python2.7 manage.py migrate --settings=mysite.settings.docker
echo "Starting development server..."
python2.7 manage.py runserver 0.0.0.0:8000 --settings=mysite.settings.docker
