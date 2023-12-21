import logging
import os
import sys

from ssh_agent_add_id.cli_arguments import CliArguments
from ssh_agent_add_id.errors import ExitCodeError
from ssh_agent_add_id.signal_handler import SignalHandler
from ssh_agent_add_id.ssh_agent import SSHAgent


def main() -> None:
    """Command line entry point."""
    args = CliArguments()

    SignalHandler()

    try:
        agent = SSHAgent()
        agent.check()

        priv_key_path = args.resolve_priv_key_path()
        pub_key_path = args.resolve_pub_key_path()

        if not agent.is_identity_stored(str(pub_key_path)):
            agent.add_identity(str(priv_key_path))

    except ExitCodeError as err:
        logging.debug(f"ExitCodeError[{err.exit_code}] cause: {type(err.__context__).__name__}")

        if err.command:
            sys.stderr.write(str(err) + os.linesep)

        sys.exit(err.exit_code)

    except BaseException as err:
        logging.debug(f"BaseException cause: {type(err.__context__).__name__}")

        err_msg = str(err)
        if err_msg:
            sys.stderr.write(err_msg + os.linesep)

        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
