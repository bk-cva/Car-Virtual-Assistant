FROM tensorflow/tensorflow:1.15.0-py3

RUN apt-get update
RUN apt install -y wget

RUN mkdir /app
RUN mkdir /models
WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache -r requirements.txt

RUN wget --no-check-certificate -O nlu_models.tar.gz \
    https://onedrive.live.com/download\?cid\=4876FFBE6BC163A8\&resid\=4876FFBE6BC163A8%212487\&authkey\=APeOuOkRDcVBY3o \
    && tar -xzvf nlu_models.tar.gz -C / \
    && rm nlu_models.tar.gz

COPY . /app

EXPOSE 5000

CMD ["./scripts/run-service.sh"]