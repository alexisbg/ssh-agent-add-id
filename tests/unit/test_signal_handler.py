from signal import Signals

import pytest
from pytest_mock.plugin import MockerFixture
from ssh_agent_add_id.errors import SignalException
from ssh_agent_add_id.signal_handler import SignalHandler


class TestInit:
    """__init__ method"""  # noqa: D415

    def test_success(self, mocker: MockerFixture) -> None:
        """Runs as expected."""
        mock_signal = mocker.patch("signal.signal")

        SignalHandler()

        assert mock_signal.call_count == 3
        assert mock_signal.mock_calls[0].args[0] == Signals.SIGHUP
        assert mock_signal.mock_calls[1].args[0] == Signals.SIGINT
        assert mock_signal.mock_calls[2].args[0] == Signals.SIGTERM


class TestHandler:
    """_handler method"""  # noqa: D415

    def test_success(self) -> None:
        """Runs as expected."""
        with pytest.raises(SignalException) as exc_info:
            SignalHandler._handler(2, None)

        assert exc_info.value.signal_num == 2
