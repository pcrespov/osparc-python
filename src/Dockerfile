ARG PYTHON_VERSION=3.8.0
FROM python:${PYTHON_VERSION}-alpine as base


LABEL maintainer=pcrespov

ENV SC_USER_ID 8004
ENV SC_USER_NAME scu

RUN adduser -D -u ${SC_USER_ID} -s /bin/sh -h /home/${SC_USER_NAME} ${SC_USER_NAME}

RUN apk add --no-cache \
            su-exec \
            bash \
            jq \
            git \
   && pip --no-cache-dir install --upgrade \
            pip \
            wheel \
            setuptools

RUN pip --no-cache-dir install \
      pipreqs

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

ENTRYPOINT [ "/bin/bash", "docker/entrypoint.sh" ]
CMD ["/bin/bash", "docker/boot.sh"]
