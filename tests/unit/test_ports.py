"""Port selection tests — default port and busy-port fallback."""

import socket

from epresso.server import DEFAULT_PORT, find_free_port


def test_default_port():
    assert DEFAULT_PORT == 4321


def test_free_port_returns_preferred():
    p = find_free_port("127.0.0.1", 54321)
    assert p == 54321


def test_busy_port_increments():
    # occupy a port, then confirm find_free_port skips it
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        busy = s.getsockname()[1]
        p = find_free_port("127.0.0.1", busy)
        assert p != busy
        assert p > busy
        # and it is actually bindable
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.bind(("127.0.0.1", p))
