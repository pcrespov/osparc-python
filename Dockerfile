ARG PYTHON_VERSION=3.8.0
FROM python:${PYTHON_VERSION}-alpine as base

LABEL maintainer=pcrespov

ENV SC_USER_ID 8004
ENV SC_USER_NAME scu
ENV INPUT_FOLDER  "/input"
ENV OUTPUT_FOLDER "/output"
ENV LOG_FOLDER    "/log"


RUN adduser -D -u ${SC_USER_ID} -s /bin/sh -h /home/${SC_USER_NAME} ${SC_USER_NAME}

# Some references:
# SEE https://hub.docker.com/r/o76923/alpine-numpy-stack/dockerfile
# SEE https://gist.github.com/orenitamar/f29fb15db3b0d13178c1c4dd611adce2
COPY src/requirements.txt /requirements.txt
RUN apk --no-cache add \
            su-exec \
            bash \
            jq \
            git \
      && pip --no-cache-dir install --upgrade \
            pip \
            wheel \
            setuptools \
      && apk --no-cache add --virtual build-deps \
            build-base \
            musl-dev \
            linux-headers \
            g++ \
            freetype-dev \
            libpng-dev \
            openblas-dev \
      && ln -s /usr/include/locale.h /usr/include/xlocale.h \
      && pip install -r /requirements.txt \
      && apk --no-cache del --purge build-deps


WORKDIR /home/${SC_USER_NAME}

# copy docker bootup scripts
COPY docker/*.sh docker/
RUN chmod +x docker/*.sh &&\
      chown ${SC_USER_NAME}:${SC_USER_NAME} docker/*.sh

# copy simcore service cli
COPY service.cli/ service.cli/
RUN chmod +x service.cli/* &&\
      chown ${SC_USER_NAME}:${SC_USER_NAME} service.cli/*

# necessary to be able to call run directly without sh in front
ENV PATH="/home/${SC_USER_NAME}/service.cli:${PATH}"

ENTRYPOINT [ "/bin/bash", "docker/entrypoint.sh" ]
CMD ["/bin/bash", "docker/boot.sh"]
