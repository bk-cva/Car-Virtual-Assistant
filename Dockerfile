FROM tensorflow/tensorflow:1.15.0-py3

RUN apt-get update
RUN apt install -y wget

RUN mkdir /app
WORKDIR /app

COPY models/vi_spacy_model-0.2.1.tar.gz /app/vi_spacy_model-0.2.1.tar.gz
RUN pip install /app/vi_spacy_model-0.2.1.tar.gz
COPY requirements.txt /app
RUN pip install --no-cache -r requirements.txt

RUN wget --no-check-certificate -O entities_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212295\&authkey\=AKsz3xMJkeCZ1oU \
    && tar -xzvf entities_models.tar.gz
RUN wget --no-check-certificate -O intents_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212294\&authkey\=AGYoTi6QuIFCY1k \
    && tar -xzvf intents_models.tar.gz

COPY scripts /app/scripts
COPY src /app/src

EXPOSE 5000

CMD ["./scripts/run-service.sh"]