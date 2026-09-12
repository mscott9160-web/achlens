"""Suite-wide security fixtures."""

import socket

import pytest


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject outbound socket attempts in every pytest test."""

    original_connect = socket.socket.connect

    def blocked_connect(self: socket.socket, address: object) -> None:
        if (
            isinstance(address, tuple)
            and address
            and address[0]
            in {
                "127.0.0.1",
                "::1",
                "localhost",
            }
        ):
            original_connect(self, address)
            return
        raise AssertionError("network access is forbidden during pytest")

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden during pytest")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
