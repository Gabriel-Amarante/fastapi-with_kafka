# pull official base image
FROM python:3.9.6-slim-buster
#FROM nvcr.io/nvidia/pytorch:21.05-py3
#MAINTAINER Matheus Pereira <matheuspereira@dcc.ufmg.br>

# set working directory
WORKDIR /usr/src/app

# set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
    && apt-get -y install kafkacat\
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN pip install --upgrade pip 
COPY ./requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# add entrypoint.sh
COPY ./entrypoint.sh .
RUN chmod +x /usr/src/app/entrypoint.sh

RUN apt update && apt install -y zip

# Install python dependencies
RUN python -m pip install --upgrade pip

RUN pip install --no-cache --upgrade tensorboard Cython onnx gsutil matplotlib \
    opencv-python pillow scipy torch torchvision tqdm \
    scikit-learn utils scikit-image
RUN pip install numpy==1.19.5
RUN pip install pytesseract
RUN export DEBIAN_FRONTEND=noninteractive && apt-get -yq install tesseract-ocr-por
RUN pip install pdfplumber==0.5.28 pdf2image nltk 
RUN apt-get install -y npm
RUN npm install difflib
RUN pip install bs4 lxml
RUN apt-get install -y poppler-utils
RUN pip install dateparser
RUN pip install fastapi
RUN pip install "uvicorn[standard]"
RUN pip install python-multipart
#RUN wget https://github.com/MPMG-DCC-UFMG/F05/archive/refs/heads/master.zip && unzip master.zip

# ENV KAFKA_HOST kafka
# ENV KAFKA_PORT 9092
# ENV KAFKA_TOPICS jobs

ENTRYPOINT ["sh", "-c","uvicorn app.main:app --host=0.0.0.0 --port=8000  --reload"]
