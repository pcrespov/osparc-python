FROM continuumio/anaconda3:2019.10
# https://hub.docker.com/r/continuumio/anaconda3/dockerfile

LABEL MAINTAINER="pcrespov"

ENV SC_USER_ID 8004
ENV SC_USER_NAME scu


## TODO: LABEL swiss.itis.ubuntu.packages="wkhtmltopdf 0.12.5;pdf-latex" ??

## TODO: add user
## Run all with


# wkhtmltopdf
# https://gist.github.com/brunogaspar/bd89079245923c04be6b0f92af431c10
RUN apt-get update --fix-missing \
    && apt-get install -y \
        xvfb \
        libfontconfig \
        wkhtmltopdf \
    && apt-get check \
    && apt-get clean

# pdf-latex
# https://gist.github.com/rain1024/98dd5e2c6c8c28f9ea9d
RUN apt-get update --fix-missing \
    && apt-get install -y \
        texlive-latex-base \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-latex-extra \
    && apt-get check \
    && apt-get clean