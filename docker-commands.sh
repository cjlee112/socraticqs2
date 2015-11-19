#!/usr/bin/env sh

echo "Clearing .pyc files."
find /code/ -name "*.pyc" -delete
echo "Done."


if [ -f /code/mysite/mysite/settings/local_conf.py ] ; then
  echo "!!!!!!!!!!!!!!!!!!!!!!\nThere is existing local_conf.py file and we do not replace it now.\nCheck DATABASE settings.\ndocker_conf.py is example for local_conf.py"
else
  echo "Copy docker_conf.py_example to local_conf.py"
  cp /code/mysite/mysite/settings/docker_conf.py_example /code/mysite/mysite/settings/local_conf.py
  echo "Done."
fi

echo "Starting development server."
python2.7 manage.py runserver 0.0.0.0:8000
