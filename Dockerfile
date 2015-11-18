FROM phusion/baseimage
RUN apt-get -y update && apt-get install -y pandoc python2.7 python-pip git libpq-dev libxml2-dev libxslt1-dev python-dev zlib1g-dev
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code/mysite
ADD . /code/
RUN pip install -r ../requirements.txt
