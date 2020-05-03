import os
import re
import logging
from flask import Flask, jsonify, make_response, request as flask_request
from flask_cors import CORS
from google.protobuf import json_format

from src.nlu import NLU
from src.proto import rest_api_pb2
from src.map import HereSDK


app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
CORS(app)
here_app = HereSDK()
nlu = NLU()


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
    # TODO: Check empty string
    try:
        proto_request = __extract_request(flask_request, rest_api_pb2.Request())
    except Exception as ex:
        return make_response(__make_json_response_error(str(ex)), 500)

    texts = proto_request.texts
    results = []
    for text in texts:
        predict_result = rest_api_pb2.PredictResult()
        intent = nlu.predict_intent(text)
        predict_result.intent = intent.name
        predict_result.entity.extend(nlu.predict_entities(text))
        results.append(predict_result)

    response = rest_api_pb2.Response()
    response.results.extend(results)
    return make_response(json_format.MessageToJson(response), 200)


@app.route('/map/suggest', methods=['POST'])
def suggest():
    try:
        proto_request = __extract_request(flask_request, rest_api_pb2.SuggestRequest())
        if not re.match(r'[\d.]+,[\d.]+', proto_request.at):
            raise ValueError('`at` must be 2 floats separated by `,`')

        at = list(map(float, proto_request.at.split(',')))
        api_results = here_app.call_autosuggest(at, proto_request.q)
        results = []
        for api_res in api_results:
            res = {'title': api_res.title, 'vicinity': api_res.vicinity, 'position': api_res.position,
                   'distance': api_res.distance, 'resultType': api_res.resultType}
            results.append(res)
        return make_response({
            'results': results,
        }, 200)
    except Exception as ex:
        return make_response(__make_json_response_error(str(ex)), 500)


def __make_json_response_error(message):
    res = rest_api_pb2.Response()
    res.error.error_message = message
    return json_format.MessageToJson(res)


def __extract_request(flask_request, request_type):
    if not flask_request.is_json:
        raise ValueError('Expecting a json request.')

    parsed_pb = json_format.Parse(flask_request.get_data(),
                                  request_type)

    return parsed_pb
