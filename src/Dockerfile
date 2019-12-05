ARG PYTHON_VERSION=3.8.0
FROM python:${PYTHON_VERSION}-alpine as base


LABEL maintainer=pcrespov


# simcore-user uid=8004(${SC_USER_NAME}) gid=8004(${SC_USER_NAME}) groups=8004(${SC_USER_NAME})
ENV SC_USER_ID 8004
ENV SC_USER_NAME scu
RUN adduser -D -u ${SC_USER_ID} -s /bin/sh -h /home/${SC_USER_NAME} ${SC_USER_NAME}

RUN apk add --no-cache \
      su-exec \
      bash \
      jq \
      git

# -------------------------- Build stage -------------------
# Installs build/package management tools and third party dependencies
#
# + /build             WORKDIR
#
FROM base as build

ENV SC_BUILD_TARGET build

RUN pip --no-cache install --upgrade \
      pip \
      wheel \
      setuptools

WORKDIR /build

COPY  src/osparc_python src/osparc_python
RUN pip --no-cache install -r src/osparc_python/requirements.txt


# --------------------------Production stage -------------------
FROM base as production

ENV SC_BUILD_TARGET production
ENV SC_BOOT_MODE production


ENV INPUT_FOLDER="/input"
ENV OUTPUT_FOLDER="/output"
ENV LOG_FOLDER="/log"


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

ENTRYPOINT [ "/bin/sh", "docker/entrypoint.sh" ]
CMD ["/bin/sh", "docker/boot.sh"]
