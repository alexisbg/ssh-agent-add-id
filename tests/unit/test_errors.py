from typing import List, cast

from pydantic import ValidationError
import pytest
from ssh_agent_add_id.errors import ExitCodeError, SignalException, _non_zero_int


class TestNonZeroInt:
    """_non_zero_int function"""  # noqa: D415

    def test_arg_type_validation_error(self) -> None:
        """Throw a ValidationError if value argument is not a integer."""
        with pytest.raises(ValidationError) as exc_info:
            _non_zero_int(cast(int, "fake"))

        assert exc_info.value.title == "_non_zero_int"
        errs = exc_info.value.errors()
        assert len(errs) == 1
        assert errs[0].get("type") == "int_type"
        #

    def test_arg_0_value_error(self) -> None:
        """Throw a ValueError if exit_code argument is equal to 0."""
        with pytest.raises(ValueError) as exc_info:
            _non_zero_int(0)

        assert exc_info.value.args[0] == "Cannot be 0"
        #

    def test_return_value(self) -> None:
        """Return the given value argument if it's a non-zero integer."""
        assert _non_zero_int(42) == 42


class TestExitCodeError:
    """ExitCodeError class"""  # noqa: D415

    def test_exit_code_arg_type_validation_error(self) -> None:
        """Throw a ValidationError if exit_code argument is not a integer."""
        with pytest.raises(ValidationError) as exc_info:
            ExitCodeError(cast(int, "fake"))

        assert exc_info.value.title == "__init__"
        errs = exc_info.value.errors()
        assert len(errs) == 1
        assert errs[0].get("type") == "int_type"
        #

    def test_exit_code_arg_0_validation_error(self) -> None:
        """Throw a ValidationError if exit_code argument is equal to 0."""
        with pytest.raises(ValidationError) as exc_info:
            ExitCodeError(0)

        assert exc_info.value.title == "__init__"
        errs = exc_info.value.errors()
        assert len(errs) == 1
        assert errs[0].get("type") == "value_error"
        assert errs[0].get("msg").endswith("Cannot be 0")
        #

    def test_command_arg_type_validation_error(self) -> None:
        """Throw a ValidationError if command argument is a string, a string list or empty."""
        with pytest.raises(ValidationError) as exc_info:
            ExitCodeError(42, cast(List[str], [True]))

        assert exc_info.value.title == "__init__"
        errs = exc_info.value.errors()
        assert len(errs) == 2
        assert errs[0].get("type") == "string_type"
        assert errs[1].get("type") == "string_type"
        #

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

    def test_arg_type_validation_error(self) -> None:
        """Throw a ValidationError if signal_num argument is not a integer."""
        with pytest.raises(ValidationError) as exc_info:
            SignalException(cast(int, "fake"))

        assert exc_info.value.title == "__init__"
        errs = exc_info.value.errors()
        assert len(errs) == 1
        assert errs[0].get("type") == "int_type"
        #

    def test_unknown_signal(self) -> None:
        """Throw a ValueError if the signal number is unknows."""
        with pytest.raises(ValueError) as exc_info:
            SignalException(4242)

        assert exc_info.value.args[0] == "4242 is not a valid Signals"
        #

    def test_success(self) -> None:
        """Run as expected."""
        err = SignalException(2)

        assert err.signal_num == 2
        assert str(err) == "SIGINT has been received"
