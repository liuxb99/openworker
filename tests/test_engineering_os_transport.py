import socket
from urllib import error as urlerror
from unittest.mock import patch

import pytest

from coworker.engineering import (
    EngineeringOSTimeoutError,
    EngineeringOSTransportError,
    UrllibEngineeringOSTransport,
)


def request(transport):
    return transport.request(
        "GET",
        "http://127.0.0.1:8080/healthz",
        body=None,
        headers={"Accept": "application/json"},
        timeout=1.0,
    )


def test_urllib_transport_normalizes_socket_timeout():
    transport = UrllibEngineeringOSTransport()
    with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
        with pytest.raises(EngineeringOSTimeoutError, match="timed out"):
            request(transport)


def test_urllib_transport_normalizes_url_error():
    transport = UrllibEngineeringOSTransport()
    with patch(
        "urllib.request.urlopen",
        side_effect=urlerror.URLError("connection refused"),
    ):
        with pytest.raises(EngineeringOSTransportError, match="connection refused"):
            request(transport)


def test_urllib_transport_classifies_timeout_wrapped_by_url_error():
    transport = UrllibEngineeringOSTransport()
    with patch(
        "urllib.request.urlopen",
        side_effect=urlerror.URLError(socket.timeout("timed out")),
    ):
        with pytest.raises(EngineeringOSTimeoutError, match="timed out"):
            request(transport)
