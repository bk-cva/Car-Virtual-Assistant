FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app

RUN pip install https://github.com/trungtv/vi_spacy/raw/master/packages/vi_spacy_model-0.2.1/dist/vi_spacy_model-0.2.1.tar.gz
ADD requirements.txt /app
RUN pip install --no-cache -r requirements.txt

COPY scripts /app/scripts
COPY src /app/src

EXPOSE 5000

CMD ["./scripts/run-service.sh"]