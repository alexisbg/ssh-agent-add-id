from signal import Signals
from typing import cast

from pydantic import ValidationError
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

    def test_arg_type_validation_error(self) -> None:
        """Throw a ValidationError if signum argument is not a integer."""
        with pytest.raises(ValidationError) as exc_info:
            SignalHandler._handler(cast(int, "fake"), None)

        assert exc_info.value.title == "_handler"
        errs = exc_info.value.errors()
        assert len(errs) == 1
        assert errs[0].get("type") == "int_type"
        #

    def test_success(self) -> None:
        """Runs as expected."""
        with pytest.raises(SignalException) as exc_info:
            SignalHandler._handler(2, None)

        assert exc_info.value.signal_num == 2
