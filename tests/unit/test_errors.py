import pytest
from ssh_agent_add_id.errors import ExitCodeError, SignalException


class TestExitCodeError:
    """ExitCodeError class"""  # noqa: D415

    def test_no_command(self) -> None:
        """Initialize without command argument."""
        err = ExitCodeError(42)

        assert err.exit_code == 42
        assert err.command is None
        assert str(err) == "Exit code 42"
        #

    def test_string_command(self) -> None:
        """Initialize with string command argument."""
        err = ExitCodeError(42, "fake_cmd")

        assert err.exit_code == 42
        assert err.command == "fake_cmd"
        assert str(err) == "Command 'fake_cmd' returned exit code 42"
        #

    def test_list_command(self) -> None:
        """Initialize with list command argument."""
        err = ExitCodeError(42, ["fake_cmd", "--test"])

        assert err.exit_code == 42
        assert err.command == "fake_cmd --test"
        assert str(err) == "Command 'fake_cmd --test' returned exit code 42"


class TestSignalException:
    """SignalException class"""  # noqa: D415

    def test_unknown_signal(self) -> None:
        """Throw a ValueError if the signal number is unknows."""
        with pytest.raises(ValueError) as exc_info:
            SignalException(4242)

        assert exc_info.value.args[0] == "4242 is not a valid Signals"
        #

    def test_init(self) -> None:
        """Run as expected."""
        err = SignalException(2)

        assert err.signal_num == 2
        assert str(err) == "SIGINT has been received"
