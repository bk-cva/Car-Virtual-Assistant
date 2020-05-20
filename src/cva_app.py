import json
import redis
import gevent
import logging
from flask_sockets import Sockets
from flask_cors import CORS
from flask import Flask, jsonify, make_response, request as flask_request
from google.protobuf import json_format

from src.proto import rest_api_pb2
from src.cva import CVA


app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
CORS(app)

sockets = Sockets(app)

REDIS_CHANNEL = 'cva'
redis = redis.from_url('redis://redis:6379/0')

cva = CVA()


class Backend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHANNEL)
    
    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info('Sending message: {}'.format(data))
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        app.logger.info('New client')
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            app.logger.info("Remove client")
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)


be = Backend()
be.start()


@app.errorhandler(500)
def server_error(e):
    app.logger.exception(str(e))
    return make_response(__make_json_response_error(str(e)), 500)


@app.route('/cva', methods=['POST'])
def cva_handler():
    request = flask_request.get_json()
    topic = request['topic']
    if topic == 'request_cva':
        user_id, utterance = [request[k] for k in ['user_id', 'utterance']]

        response, metadata, intent, entities = cva(utterance)
        redis.publish(REDIS_CHANNEL, json.dumps({
            'user_id': user_id,
            'utterance': utterance,
            'response': response,
            'metadata': metadata,
            'intent': intent,
            'entities': entities
        }, default=lambda x: x.__dict__))
    elif topic == 'reset_cva':
        cva.reset()
    else:
        raise Exception('Unknown topic.')
    return make_response(jsonify({
        'status': 'ok'
    }), 200)


@sockets.route('/')
def outbox(ws):
    be.register(ws)

    while not ws.closed:
        gevent.sleep(0.1)


def __make_json_response_error(message):
    res = rest_api_pb2.Response()
    res.error.error_message = message
    return json_format.MessageToJson(res)
