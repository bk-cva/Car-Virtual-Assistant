import logging

from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

from src.nlp import predict_intent, predict_entity

app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
CORS(app)


@app.errorhandler(404)
def url_error(e):
    return make_response(jsonify({'message': str(e)}), 404)


@app.errorhandler(500)
def server_error(e):
    return make_response(jsonify({'message': str(e)}), 500)


@app.route('/healthz', methods=['GET'])
def health_check_route():
    return make_response(jsonify({
        'status': 'I am healthy, thanks for asking!'
    }), 200)


@app.route('/analyze', methods=['POST'])
def analyze():
    body = request.get_json()
    texts = body['texts']
    results = [{
        'intent': predict_intent(text),
        'entity': predict_entity(text)
    } for text in texts]

    return make_response(jsonify({'results': results}), 200)
