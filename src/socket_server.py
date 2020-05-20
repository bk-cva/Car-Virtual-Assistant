import os
import json
import logging
import asyncio
import websockets

from src.cva import CVA


PORT = os.getenv('PORT', 3000)
cva = CVA()


async def handler(websocket, path):
    while True:
        try:
            payload = json.loads(await websocket.recv())
            topic = payload['topic']
            if topic == 'request_cva':
                user_id, utterance = [payload[k] for k in ['user_id', 'utterance']]

                response, metadata, intent, entities = cva(utterance)

                await websocket.send(json.dumps({
                    'user_id': user_id,
                    'response': response,
                    'metadata': metadata,
                    'intent': intent,
                    'entities': entities
                }, default=lambda x: x.__dict__))
            elif topic == 'reset_cva':
                cva.reset()
            else:
                raise Exception('Unknown topic.')
        except Exception as e:
            logging.exception(str(e))
            await websocket.send(json.dumps({
                'error': str(e),
            }))

start_server = websockets.serve(handler, "0.0.0.0", PORT)

print('========================================\n')
print('Server is listening at port {}.'.format(PORT))
print('\n========================================')
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
