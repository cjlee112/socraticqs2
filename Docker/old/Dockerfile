FROM node:8 as static

COPY mysite/draw_svg /tmp/mysite/draw_svg
COPY mysite/frontend /tmp/mysite/frontend

WORKDIR /tmp/mysite/draw_svg

RUN npm install && npm rebuild node-sass
RUN yarn build && yarn build:copy-prebuild

WORKDIR /tmp/mysite/frontend
RUN yarn


FROM python:2.7-slim as base

RUN groupadd courselets && useradd --create-home --home-dir /home/courselets -g courselets courselets

RUN apt-get -y update && \
    apt-get install -y \
    git \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements ./requirements

RUN pip install --upgrade pip setuptools
RUN pip install --ignore-installed -U -r /requirements/base.txt
RUN pip install --ignore-installed -U -r /requirements/prod.txt

ENV PYTHONUNBUFFERED 1

WORKDIR /home/courselets/app/mysite
RUN chown -R courselets:courselets /home/courselets
# RUN groupadd courselets && useradd --create-home --home-dir /home/courselets -g courselets courselets

# RUN chown -R celery:celery /home/celery/

# USER user
COPY celeryconfig.py ./
# ENV CELERY_BROKER_URL amqp://guest@rabbit

# ONBUILD ADD . /app
# ONBUILD COPY --from=static /drawing.bundle.js lms/static/js/drawing.bundle.js
# ONBUILD COPY --from=static /tmp/mysite/frontend/bower_components chat/static/bower_components

# # ONBUILD WORKDIR /app/mysite

# ONBUILD COPY docker-entrypoint.sh /usr/local/bin/
# ONBUILD RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# ONBUILD ENTRYPOINT ["docker-entrypoint.sh"]


FROM base as prod

ADD . /home/courselets/app
# COPY --from=static /drawing.bundle.js lms/static/js/drawing.bundle.js
# COPY --from=static /tmp/mysite/frontend/bower_components chat/static/bower_components

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN chown -R courselets:courselets /home/courselets
USER courselets

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["prod"]


FROM base as test

RUN apt-get -y update && \
	apt-get install -y \
	gcc \
	make \
	python-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --ignore-installed -U -r /requirements/test.txt

ADD . /home/courselets/app
# COPY --from=static /drawing.bundle.js lms/static/js/drawing.bundle.js
# COPY --from=static /tmp/mysite/frontend/bower_components chat/static/bower_components

RUN chown -R courselets:courselets /home/courselets

FROM base as dev

RUN apt-get -y update && \
	apt-get install -y \
	libpq-dev \
	libxml2-dev \
	libxslt1-dev \
	make \
	phantomjs \
	python-dev \
	wget \
	zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/*
RUN pip install --ignore-installed -U -r /requirements/dev.txt

ADD . /home/courselets/app
# COPY --from=static /drawing.bundle.js lms/static/js/drawing.bundle.js
# COPY --from=static /tmp/mysite/frontend/bower_components chat/static/bower_components

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN chown -R courselets:courselets /home/courselets
USER courselets

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["dev"]


FROM prod
