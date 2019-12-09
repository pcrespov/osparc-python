FROM continuumio/anaconda3:2019.10
# https://hub.docker.com/r/continuumio/anaconda3/dockerfile


RUN apt-get update --fix-missing \
    && apt-get install -y \
        xvfb \
        libfontconfig \
        wkhtmltopdf

# Test with: wkhtmltopdf http://www.google.com google.pdf

# pdf-latex
RUN apt-get update --fix-missing \
    && apt-get install -y \
        texlive-latex-base \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-latex-extra \
    && apt-get clean