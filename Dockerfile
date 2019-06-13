FROM node:8 as builder

WORKDIR /tmp
COPY . .

WORKDIR /tmp/mysite/draw_svg

RUN npm install && npm rebuild node-sass
RUN yarn build && yarn build:copy-prebuild

WORKDIR /tmp/mysite/frontend
RUN yarn


FROM python:2.7-slim
LABEL maintainer="cmltaWt0@gmail.com"

RUN apt-get -y update && \
    apt-get install -y \
    wget \
    pandoc \
    make \
    git \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    python-dev \
    zlib1g-dev \
    phantomjs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements ./requirements

RUN pip install --upgrade pip setuptools
RUN pip install --ignore-installed -U -r /requirements/dev.txt
RUN pip install --ignore-installed -U -r /requirements/prod.txt

ENV PYTHONUNBUFFERED 1

RUN mkdir /app
ADD . /app
COPY --from=builder /draw_svg.js /app/mysite/lms/static/js/draw_svg.js
COPY --from=builder /draw_svg.css /app/mysite/lms/static/css/draw_svg.css
COPY --from=builder /tmp/mysite/frontend/bower_components /app/mysite/chat/static/bower_components

WORKDIR /app/mysite
