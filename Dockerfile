FROM python:3.7-slim

RUN apt-get update
RUN apt install -y wget

RUN mkdir /app
WORKDIR /app

COPY models/vi_spacy_model-0.2.1.tar.gz /app/vi_spacy_model-0.2.1.tar.gz
RUN pip install /app/vi_spacy_model-0.2.1.tar.gz
COPY requirements.txt /app
RUN pip install --no-cache -r requirements.txt

RUN wget --no-check-certificate -O entities_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212280\&authkey\=AHPfexVWvH2Ox-Q \
    && tar -xzvf entities_models.tar.gz
RUN wget --no-check-certificate -O intents_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212279\&authkey\=AMcmzuAiqU-75-I \
    && tar -xzvf intents_models.tar.gz

COPY scripts /app/scripts
COPY src /app/src

EXPOSE 5000

CMD ["./scripts/run-service.sh"]