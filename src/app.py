import logging

from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

from src.nlp.intent_classification.classify import classify_intent


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


@app.route('/intent', methods=['POST'])
def get_intent():
    body = request.get_json()
    texts = body['texts']
    results = [classify_intent(text) for text in texts]

    return make_response(jsonify({'results': results}), 200)
