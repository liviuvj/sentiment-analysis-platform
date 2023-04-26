FROM python:3.9

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential cmake libgtk-3-dev libboost-all-dev libssl-dev \
    libcurl4-openssl-dev libhdf5-dev libbz2-dev liblzma-dev libblas-dev \
    liblapack-dev libffi-dev libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir datasets scikit-learn pandas \
    numpy torch pymongo boto3 spacy seaborn matplotlib transformers

# RUN python -m spacy download en_core_web_sm
