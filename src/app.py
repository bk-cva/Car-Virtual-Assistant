import logging
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from google.protobuf import json_format

from src.nlp import predict_intent, predict_entity
from src.proto import rest_api_pb2

app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
CORS(app)


@app.errorhandler(404)
def url_error(e):
    response = rest_api_pb2.Response()
    response.error.error_message = str(e)
    return make_response(json_format.MessageToJson(response), 404)


@app.errorhandler(500)
def server_error(e):
    response = rest_api_pb2.Response()
    response.error.error_message = str(e)
    return make_response(json_format.MessageToJson(response), 500)


@app.route('/healthz', methods=['GET'])
def health_check_route():
    return make_response(jsonify({
        'status': 'I am healthy, thanks for asking!'
    }), 200)


@app.route('/analyze', methods=['POST'])
def analyze():
    body = request.get_json()
    texts = body['texts']
    results = []
    for text in texts:
        predict_result = rest_api_pb2.PredictResult()
        intent = predict_intent(text)
        predict_result.intent_id = intent
        predict_result.intent = intent.name
        predict_result.entity.extend(predict_entity(text))
        results.append(predict_result)

    response = rest_api_pb2.Response()
    response.results.extend(results)
    return make_response(json_format.MessageToJson(response), 200)
