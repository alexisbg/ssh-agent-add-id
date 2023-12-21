import getpass
import logging
import os
import shlex
import shutil
from signal import SIGINT
from subprocess import PIPE, CalledProcessError, Popen
import sys
from typing import Optional, Union

from pexpect import EOF, TIMEOUT, spawn

from ssh_agent_add_id.errors import ExitCodeError, SignalException


class SSHAgent:
    """Manage SSH agent identities."""

    def check(self) -> None:
        """Check if SSH agent is ready for use.

        Raises:
            FileNotFoundError: ssh-add command is not reachable or not installed.
            ValueError: SSH_AUTH_SOCK environment variable is not reachable or not set.
        """
        # Check if ssh-add is installed
        ssh_add_path = shutil.which("ssh-add")
        if not ssh_add_path:
            raise FileNotFoundError("ssh-add command not found")

        logging.debug(f"ssh-add command path: {ssh_add_path}")

        # Check if SSH_AUTH_SOCK is defined
        agent_sock = os.getenv("SSH_AUTH_SOCK")
        if not agent_sock:
            raise ValueError(
                "SSH_AUTH_SOCK not found. If ssh-agent has been started, \
                    can the current environment read this variable?"
            )

        logging.debug(f"SSH_AUTH_SOCK value: {agent_sock}")
        #

    def add_identity(self, priv_key_path: str) -> None:
        """Add identity to the SSH agent.

        Args:
            priv_key_path (str): The private key path of the identity.

        Raises:
            ExitCodeError: If ssh-add exit code is not zero or a signal has been received.
            SignalException: If a signal has been received.
            RuntimeError: If ssh-add does not run as expected.
        """
        cmd = f"ssh-add {priv_key_path}"
        logging.debug(f"add_identity command: {cmd}")

        child: Optional[spawn] = None

        try:
            child = spawn(cmd, encoding="utf-8")

            while True:
                try:
                    index = child.expect(
                        [
                            "Enter passphrase for.*",
                            "Bad passphrase, try again for.*",
                            "Identity added.*",
                        ],
                        timeout=1,  # fails with 0
                    )

                    logging.debug(f"add_identity expect index: {index}")
                    logging.debug(f"add_identity before: {child.before}")
                    logging.debug(f"add_identity after: {child.after}")

                    sys.stdout.write(child.after)

                    # Calling flush() is required in order for printing to work
                    sys.stdout.flush()

                    if index in [0, 1]:
                        passphrase = getpass.getpass("")
                        if not passphrase:
                            # Since ssh-add stops if the passphrase is empty, we send it a bad one.
                            passphrase = ">P_F&DFdbob20m5wl`e;ARviU@Lb>*(Uuw_?A~0cILXPlDU8f;"

                        logging.debug(f"add_identity passphrase: {passphrase}")

                        child.sendline(passphrase)

                except (EOF, TIMEOUT) as err:
                    logging.debug(f"add_identity expect exception: {type(err).__name__}")

                    child.close()

                    if child.before:  # Get message from stderr before exception
                        sys.stderr.write(child.before)

                    if child.exitstatus:
                        raise ExitCodeError(child.exitstatus, cmd)
                    if child.signalstatus:
                        raise SignalException(child.signalstatus)
                    if isinstance(err, TIMEOUT):
                        raise RuntimeError("ssh-add did not run as expected")

                    # EOF without failure
                    return

        # A signal has been received
        except SignalException as err:
            if child and child.isalive():
                child.sendintr()
                child.wait()

            sys.stderr.write(f"{os.linesep}{err}{os.linesep}")
            raise ExitCodeError(130)

        # Rethrow all unknown exception
        except:
            raise

        finally:
            if child and child.isalive():
                child.close()
                #

    def is_identity_stored(self, pub_key_path: str) -> bool:
        """Search for the given identity among all those currently stored by the SSH agent.

        Args:
            pub_key_path (str): The public key path of the identity.

        Raises:
            ExitCodeError: If ssh-add exit code is not zero or a signal has been received.
            RuntimeError: If ssh-add process is still alive.
            CalledProcessError: If ssh-add process fails.
            ValueError: If :attr:`subprocess.Popen.returncode` value is not an `int` or `None`.

        Returns:
            bool: True if the given public key matches an identity stored by the SSH agent.
        """
        cmd = f"ssh-add -T {pub_key_path}"
        logging.debug(f"is_identity_stored command: {cmd}")

        popen: Optional[Popen] = None

        try:
            popen = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
            stdout, stderr = popen.communicate()

            logging.debug(f"is_identity_stored returncode: {popen.returncode}")
            logging.debug(f"is_identity_stored stdout: {stdout}")
            logging.debug(f"is_identity_stored stderr: {stderr}")

            assert popen.returncode is None or isinstance(popen.returncode, int)

            if popen.returncode == 0:
                print("This identity has already been added to the SSH agent.")
                return True
            elif popen.returncode == 1 and "Agent signature failed for" in str(stderr):
                # ID not stored by agent
                return False
            elif popen.returncode and popen.returncode >= 1:
                raise CalledProcessError(popen.returncode, popen.args, stdout, stderr)
            elif popen.returncode is None:
                raise RuntimeError("ssh-add did not terminate as expected")
            else:
                rc = popen.returncode
                raise ValueError(f"Unexpected Popen returncode value: [{type(rc).__name__}] {rc}")

        except CalledProcessError as err:
            if err.stdout:
                sys.stdout.write(self._append_nl(err.stdout))
            if err.stderr:
                sys.stderr.write(self._append_nl(err.stderr))

            raise ExitCodeError(err.returncode, shlex.join(err.cmd))

        # A signal has been received
        except SignalException as err:
            if popen and popen.poll() is None:
                popen.send_signal(SIGINT)
                popen.wait()

            sys.stderr.write(f"{os.linesep}{err}{os.linesep}")
            raise ExitCodeError(130)

        # Rethrow all unknown exceptions
        except:
            raise

        finally:
            if popen and popen.poll() is None:
                popen.terminate()
                #

    def _append_nl(self, message: Union[bytes, str]) -> str:
        """Append a newline at the end of the message if there is none.

        Args:
            message (Union[bytes, str]): The bytes or the string of the message.

        Raises:
            TypeError: If the given message argument is not bytes or a string.

        Returns:
            str: An UTF-8 string ending with a newline.
        """
        if not isinstance(message, (bytes, str)):
            raise TypeError(
                "The given message is not bytes or a string but " + type(message).__name__
            )

        if isinstance(message, bytes):
            out: str = message.decode()
        else:
            out: str = message

        if out.endswith("\n"):
            return out
        else:
            return out + os.linesep
