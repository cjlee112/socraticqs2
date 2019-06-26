FROM python:2.7-slim

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

RUN groupadd courselets && useradd --create-home --home-dir /home/courselets -g courselets courselets

WORKDIR /home/courselets/app/mysite
RUN chown -R courselets:courselets /home/courselets

COPY celeryconfig.py ./
COPY .conf /home/courselets/app/.conf
# ADD mysite /home/courselets/app/mysite
# ONBUILD COPY --from=static /draw_svg.js lms/static/js/draw_svg.js
# ONBUILD COPY --from=static /draw_svg.css lms/static/css/draw_svg.css
# ONBUILD COPY --from=static /tmp/mysite/frontend/bower_components chat/static/bower_components

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
