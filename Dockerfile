FROM tensorflow/tensorflow:1.15.0-py3

RUN apt-get update
RUN apt install -y wget

RUN mkdir /app
RUN mkdir /models
WORKDIR /app

COPY models /models
RUN pip install /models/vi_spacy_model-0.2.1.tar.gz
COPY requirements.txt /app
RUN pip install --no-cache -r requirements.txt


RUN wget --no-check-certificate -O entities_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212394\&authkey\=AKBvgUDQ-R-vdX4 \
    && tar -xzvf entities_models.tar.gz -C / \
    && rm entities_models.tar.gz
RUN wget --no-check-certificate -O intents_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212393\&authkey\=AH5ViQNkNwy9BJ0 \
    && tar -xzvf intents_models.tar.gz -C / \
    && rm intents_models.tar.gz

COPY . /app

EXPOSE 5000

CMD ["./scripts/run-service.sh"]