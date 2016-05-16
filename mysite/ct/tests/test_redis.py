"""
Module to test docker with py.test.
"""

import time
import uuid
import socket

import redis
import pytest
import docker as libdocker


@pytest.fixture(scope='session')
def unused_port():
    def factory():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]
    return factory


@pytest.fixture(scope='session')
def session_id():
    return str(uuid.uuid4())


@pytest.fixture(scope='session')
def docker():
    return libdocker.Client(version='auto')


@pytest.yield_fixture(scope='session')
def redis_server(unused_port, session_id, docker):
    docker.pull('redis:latest')
    port = unused_port()
    container = docker.create_container(
        image='redis',
        name='test-redis-{}'.format(session_id),
        ports=[6379],
        detach=True,
        host_config=docker.create_host_config(
            port_bindings={6379: port}))
    docker.start(container=container['Id'])
    yield port
    docker.kill(container=container['Id'])
    docker.remove_container(container['Id'])


@pytest.fixture
def redis_client(redis_server):
    for i in range(100):
        try:
            client = redis.StrictRedis(host='127.0.0.1',
                                       port=redis_server, db=0)
            # open connection to redis
            client.get('some_key')
            return client
        except redis.ConnectionError:
            time.sleep(0.01)


def test_redis(redis_client):
    redis_client.set(b'key', b'value')
    assert redis_client.get(b'key') == b'value'
