import logging
from flask import Flask, jsonify, make_response, request as flask_request
from flask_cors import CORS
from google.protobuf import json_format

from src.nlu import predict_intent, predict_entity
from src.proto import rest_api_pb2

app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
CORS(app)


@app.errorhandler(404)
def url_error(e):
    return make_response(__make_json_response_error(str(e)), 404)


@app.errorhandler(500)
def server_error(e):
    return make_response(__make_json_response_error(str(e)), 500)


@app.route('/healthz', methods=['GET'])
def health_check_route():
    return make_response(jsonify({
        'status': 'I am healthy, thanks for asking!'
    }), 200)


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        proto_request = __extract_request(flask_request)
    except Exception as ex:
        return make_response(__make_json_response_error(str(ex)), 500)

    texts = proto_request.texts
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


def __make_json_response_error(message):
    res = rest_api_pb2.Response()
    res.error.error_message = message
    return json_format.MessageToJson(res)


def __extract_request(flask_request):
    if not flask_request.is_json:
        raise ValueError('Expecting a json request.')

    parsed_pb = json_format.Parse(flask_request.get_data(),
                                  rest_api_pb2.Request())
    # Checks required fields.
    if not parsed_pb.texts:
        raise ValueError('Expecting at least one document.')

    return parsed_pb
