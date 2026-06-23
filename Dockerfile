FROM python:alpine3.19

LABEL maintainer="tomasz.szymanski@greenit.com.pl"
ARG BUILD_DATE

RUN mkdir /code
COPY graylog_config_checker.py graylog_permission_checker.py requirements.txt /code/.
WORKDIR /code

RUN pip install -r requirements.txt

ENTRYPOINT ["/code/graylog_config_checker.py"]

# LABELS
# BUILD_DATE: date -u +'%Y-%m-%dT%H:%M:%SZ'
# use build-arg with docker build
# docker build --no-cache=true --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') -t graylog_config_checker:latest .
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.version=1.0.0
LABEL org.opencontainers.image.title='graylog_config_checker'
LABEL org.opencontainers.image.description='Graylog Config Checker'
LABEL org.opencontainers.image.vendor='GreenIT'

