FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app

COPY src/nlp/intents/vi_spacy_model-0.2.1.tar.gz /app/vi_spacy_model-0.2.1.tar.gz
RUN pip install /app/vi_spacy_model-0.2.1.tar.gz
COPY requirements.txt /app
RUN pip install --no-cache -r requirements.txt

COPY scripts /app/scripts
COPY src /app/src

EXPOSE 5000

CMD ["./scripts/run-service.sh"]