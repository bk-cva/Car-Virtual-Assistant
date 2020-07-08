from src.proto.rest_api_pb2 import Entity


def entity_factory(name: str, value: str):
    entity = Entity()
    entity.name = name
    entity.value = value
    return entity
