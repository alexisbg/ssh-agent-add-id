from argparse import ArgumentParser, Namespace
import logging
from pathlib import Path
import sys
from typing import Optional

from ssh_agent_add_id import __version__
from ssh_agent_add_id.constants import APP_DESCRIPTION, APP_NAME


class CliArguments:
    """Parse and resolve the CLI arguments."""

    _args: Namespace
    _priv_key_path: Optional[Path] = None
    _pub_key_path: Optional[Path] = None

    def __init__(self) -> None:
        """Setup an :class:`argparse.ArgumentParser` and parse the given CLI arguments."""
        parser = ArgumentParser(prog=APP_NAME, description=APP_DESCRIPTION)

        # fmt: off
        parser.add_argument("priv_key_path", help="the path of the private key file")
        parser.add_argument("pub_key_path", nargs="?",
            help="the path of the public key file in case its filename is not <priv_key_path>.pub")
        parser.add_argument("--verbose", action="store_true", help="print some extra info")
        parser.add_argument("--version", action="version", version=f"{parser.prog} {__version__}")
        # fmt: on

        self._args = parser.parse_args()

        log_level = logging.DEBUG if self._args.verbose else logging.ERROR
        logging.basicConfig(format="%(message)s", level=log_level, stream=sys.stdout)

        logging.debug(f"args: {self._args._get_kwargs()}")
        #

    def resolve_priv_key_path(self) -> Path:
        """Get the Path object of the private key from the priv_key_path argument.

        Raises:
            FileNotFoundError: If the resulting path does not exist.

        Returns:
            Path: The resolved Path object of the private key.
        """
        if not self._priv_key_path:
            self._priv_key_path = Path(self._args.priv_key_path).expanduser().resolve()
            if not self._priv_key_path.exists():
                raise FileNotFoundError(f"{self._priv_key_path} not found")

        logging.debug(f"resolve_priv_key_path: {self._priv_key_path}")

        return self._priv_key_path
        #

    def resolve_pub_key_path(self) -> Path:
        """Get the Path object of the public key from the priv_key_path or pub_key_path arguments.

        Raises:
            FileNotFoundError: If the resulting path does not exist.

        Returns:
            Path: The resolved Path object of the public key.
        """
        if not self._pub_key_path:
            # There is pub_key_path argument
            if self._args.pub_key_path:
                self._pub_key_path = Path(self._args.pub_key_path).expanduser().resolve()

            # Concat .pub to priv_key_path argument
            else:
                priv_key_path = self._priv_key_path
                if not priv_key_path:
                    priv_key_path = self.resolve_priv_key_path()
                self._pub_key_path = priv_key_path.with_suffix(".pub")

            if not self._pub_key_path.exists():
                raise FileNotFoundError(f"{self._pub_key_path} not found")

        logging.debug(f"resolve_pub_key_path: {self._pub_key_path}")

        return self._pub_key_path
