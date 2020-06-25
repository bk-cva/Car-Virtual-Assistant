import json
import redis
import gevent
import logging
from flask_sockets import Sockets
from flask_cors import CORS
from flask import Flask, make_response, request as flask_request
from flask.json import dumps
from google.protobuf import json_format
from datetime import date, datetime

from src.proto import rest_api_pb2
from src.cva import CVA
from src.config_manager import ConfigManager


fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
fh.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)

app = Flask(__name__)
CORS(app)

sockets = Sockets(app)

REDIS_CHANNEL = 'cva'
redis = redis.from_url('redis://redis:6379/0')

do_call_external_nlu = ConfigManager().get('DO_CALL_EXTERNAL_NLU') == 'true'
cva = CVA(do_call_external_nlu=do_call_external_nlu)


class Broker(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHANNEL)
    
    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                logger.info('Sending message: {}'.format(data))
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        logger.info('New client')
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            logger.info("Remove client")
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)


broker = Broker()
broker.start()


@app.errorhandler(500)
def server_error(e):
    logger.exception(str(e))
    return make_response(__make_json_response_error(str(e)), 500)


@app.route('/cva', methods=['POST'])
def cva_handler():
    request = flask_request.get_json()
    topic = request['topic']
    data = {}
    if topic == 'request_cva':
        user_id, utterance = [request[k] for k in ['user_id', 'utterance']]
        response, metadata, intent, action = cva(utterance)

        data = {
            'topic': 'message',
            'user_id': user_id,
            'utterance': utterance,
            'response': response,
            'metadata': metadata,
            'intent': intent,
            'action': action,
        }

        redis.publish(REDIS_CHANNEL, json.dumps(data, default=json_serial))
    elif topic == 'reset_cva':
        cva.reset()
        redis.publish(REDIS_CHANNEL, json.dumps({
            'topic': 'reset',
        }))
    else:
        raise Exception('Unknown topic.')

    response = make_response(
        dumps({
            'status': 'ok',
            **data}, default=json_serial),
        200)
    response.headers['Content-type'] = 'application/json; charset=utf-8'
    return response


@sockets.route('/')
def outbox(ws):
    broker.register(ws)

    while not ws.closed:
        gevent.sleep(0.1)


def __make_json_response_error(message):
    res = rest_api_pb2.Response()
    res.error.error_message = message
    return json_format.MessageToJson(res)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj.__dict__
