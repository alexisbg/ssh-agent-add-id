import signal
from typing import List, Optional, Union

from pydantic import ConfigDict, PlainValidator, validate_call
from typing_extensions import Annotated


@validate_call(config=ConfigDict(strict=True))
def _non_zero_int(value: int) -> int:
    """Throw a ValueError if the given `int` is equal to 0."""
    if value == 0:
        raise ValueError("Cannot be 0")
    return value


NonZeroInt = Annotated[int, PlainValidator(_non_zero_int)]


class ExitCodeError(Exception):  # noqa: D101
    @validate_call(config=ConfigDict(strict=True))
    def __init__(self, exit_code: NonZeroInt, command: Union[str, List[str], None] = None) -> None:
        """Raised when the exit code of the given command indicates a failure.

        Args:
            exit_code (int): The exit code returned by the command. It can not be equal to 0.
            command (str): The command that has been executed.

        Raises:
            ValidationError: If an argument type is not valid.
        """
        self.exit_code: int = exit_code

        self.command: Optional[str] = None
        err_msg = f"Exit code {exit_code}"
        if command:
            if isinstance(command, list):
                self.command = " ".join(command)
            else:
                self.command = command
            err_msg = f"Command '{self.command}' returned exit code {exit_code}"

        super().__init__(err_msg)


class SignalException(Exception):  # noqa: D101
    @validate_call(config=ConfigDict(strict=True))
    def __init__(self, signal_num: int) -> None:
        """Notify that a given signal has been received.

        Args:
            signal_num (int): The integer value of a signal from signal.Signals enum.

        Raises:
            ValidationError: If an argument type is not valid.
        """
        self.signal_num: int = signal_num

        super().__init__(f"{signal.Signals(signal_num).name} has been received")
