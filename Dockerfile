FROM itisfoundation/python-anaconda:3.7

LABEL maintainer=pcrespov

ENV INPUT_FOLDER  "/input"
ENV OUTPUT_FOLDER "/output"
ENV LOG_FOLDER    "/log"

ENV SC_BUILD_TARGET production
ENV SC_USER_ID 8004
ENV SC_USER_NAME scu

RUN adduser \
      --uid ${SC_USER_ID} \
      --disabled-password \
      --gecos "" \
      --shell /bin/bash \
      --home /home/${SC_USER_NAME} \
      ${SC_USER_NAME}


WORKDIR /home/${SC_USER_NAME}

COPY --chown=scu:scu src/ src/

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
