import signal
from typing import Any

from pydantic import ConfigDict, validate_call

from ssh_agent_add_id.errors import SignalException


class SignalHandler:
    """Raise a SignalError when some signals are received."""

    def __init__(self) -> None:
        """Define a custom handler for some signals."""
        signal.signal(signal.SIGHUP, SignalHandler._handler)
        signal.signal(signal.SIGINT, SignalHandler._handler)
        signal.signal(signal.SIGTERM, SignalHandler._handler)
        #

    @staticmethod
    @validate_call(config=ConfigDict(strict=True))
    def _handler(signum: int, frame: Any) -> None:  # noqa: ANN401
        """The signal handler throws a SignalException when it is called.

        Args:
            signum (int): The integer value of a signal.
            frame (Any): Required by the signal handler signature.

        Raises:
            ValidationError: If an argument type is not valid.
        """
        raise SignalException(signum)
