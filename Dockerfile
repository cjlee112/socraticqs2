# Dockerfile to inject app source code into Image
FROM maxsocl/courselets:dev
CMD find . -name '*.pyc' -delete
ADD . /code/
