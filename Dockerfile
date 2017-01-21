# Dockerfile to inject app source code into Image
FROM maxsocl/courselets:latest
CMD find . -name '*.pyc' -delete
ADD . /code/
