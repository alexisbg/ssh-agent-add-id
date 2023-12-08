import getpass
import os
import shlex
import shutil
from signal import SIGINT
from subprocess import PIPE, CalledProcessError, Popen
import sys
from typing import Optional

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
        if not shutil.which("ssh-add"):
            raise FileNotFoundError("ssh-add command not found")

        # Check if SSH_AUTH_SOCK is defined
        agent_sock = os.getenv("SSH_AUTH_SOCK")
        if not agent_sock:
            raise ValueError(
                "SSH_AUTH_SOCK not found. If ssh-agent has been started, \
                    can the current environment read this variable?"
            )
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

                    sys.stdout.write(child.after)

                    if index in [0, 1]:
                        passphrase = getpass.getpass("")
                        if not passphrase:
                            # Since ssh-add stops if the passphrase is empty, we send it a bad one.
                            passphrase = ">P_F&DFdbob20m5wl`e;ARviU@Lb>*(Uuw_?A~0cILXPlDU8f;"
                        child.sendline(passphrase)

                except (EOF, TIMEOUT) as err:
                    child.close()
                    if child.exitstatus:
                        raise ExitCodeError(child.exitstatus, cmd)
                    if child.signalstatus:
                        raise SignalException(child.signalstatus)
                    if isinstance(err, TIMEOUT):
                        raise RuntimeError("ssh-add did not run as expected")

                    return

        # A signal has been received
        except SignalException as err:
            if child and child.isalive():
                child.sendintr()
                child.wait()

            sys.stderr.write(f"\n{err}\n")
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
        popen: Optional[Popen] = None

        try:
            popen = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
            stdout, stderr = popen.communicate()

            assert popen.returncode is None or isinstance(popen.returncode, int)

            if popen.returncode == 0:
                print("This identity has already been added to the SSH agent.")
                return True
            elif popen.returncode == 1:
                return False  # The exit code is 1 if the list is empty
            elif popen.returncode and popen.returncode > 1:
                raise CalledProcessError(popen.returncode, popen.args, stdout, stderr)
            elif popen.returncode is None:
                raise RuntimeError("ssh-add did not terminate as expected")
            else:
                rc = popen.returncode
                raise ValueError(f"Unexpected Popen returncode value: [{type(rc).__name__}] {rc}")

        except CalledProcessError as err:
            if err.stdout:
                sys.stdout.write(str(err.stdout) + "\n")
            if err.stderr:
                sys.stderr.write(str(err.stderr) + "\n")

            raise ExitCodeError(err.returncode, cmd)

        # A signal has been received
        except SignalException as err:
            if popen and popen.poll() is None:
                popen.send_signal(SIGINT)
                popen.wait()

            sys.stderr.write(f"\n{err}\n")
            raise ExitCodeError(130)

        # Rethrow all unknown exceptions
        except:
            raise

        finally:
            if popen and popen.poll() is None:
                popen.terminate()
