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

COPY --chown=courselets:courselets celeryconfig.py ./
COPY --chown=courselets:courselets .conf /home/courselets/app/.conf

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
