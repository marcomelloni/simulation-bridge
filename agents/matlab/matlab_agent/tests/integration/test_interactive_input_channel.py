import yaml
from queue import Queue
from unittest.mock import MagicMock

from src.core.interactive import handle_interactive_input, MatlabInteractiveController


def test_handle_interactive_input_forwards_to_queue():
    q = Queue()
    body = yaml.dump({'simulation': {'inputs': {'a': 1}}}).encode()
    handle_interactive_input(None, None, None, body, q)
    assert not q.empty()
    assert q.get()['simulation']['inputs']['a'] == 1

def test_run_sends_queue_messages(monkeypatch):
    mq = MagicMock()
    mq.channel = MagicMock()
    mq.channel.exchange_declare.return_value = None
    mq.channel.queue_declare.return_value = None
    mq.channel.queue_bind.return_value = None
    mq.channel.basic_consume.side_effect = lambda **kwargs: None
    controller = MatlabInteractiveController(
        '.', 'file.m', 'src', mq, {},
        {'host': 'localhost', 'port': 5000, 'input_host': 'localhost', 'input_port': 5001},
        'meta', 'req', 'agent'
    )
    controller.connection = MagicMock()
    controller.input_connection = MagicMock()
    controller.connection.receive.return_value = []
    controller.connection.accept_connection = MagicMock()
    controller.input_connection.accept_connection = MagicMock()
    monkeypatch.setattr('src.core.interactive.Queue', Queue)
    q = Queue()
    handle_interactive_input(None, None, None, yaml.dump({'val': 1}).encode(), q)
    controller.command_producer = lambda q, delay=0.5: None
    monkeypatch.setattr('src.core.interactive.Queue', lambda: q)
    controller.run({}, MagicMock(), {'simulation': {'inputs': {'stream_source': ''}}}, 'req')
    controller.input_connection.send.assert_called()
