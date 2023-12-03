from signal import SIGINT
from subprocess import CalledProcessError
from typing import cast

from pexpect import EOF, TIMEOUT
import pytest
from pytest_mock.plugin import MockerFixture, MockType
from ssh_agent_add_id.errors import ExitCodeError, SignalException
from ssh_agent_add_id.ssh_agent import SSHAgent


class TestAddIdentity:
    """add_identity method"""  # noqa: D415

    class Mocks:
        """Some mocks for the tests."""

        def __init__(self, mocker: MockerFixture) -> None:  # noqa: D107
            self.mocker = mocker

            self.spawn = mocker.patch("ssh_agent_add_id.ssh_agent.spawn")
            self.child: MockType = self.spawn.return_value
            self.child.exitstatus = 0
            self.child.signalstatus = 0
            self.close: MockType = self.child.close
            self.expect: MockType = self.child.expect
            self.isalive: MockType = self.child.isalive
            self.isalive.return_value = True
            self.sendintr: MockType = self.child.sendintr
            self.sendline: MockType = self.child.sendline
            #

    @pytest.fixture
    def mocks(self, mocker: MockerFixture) -> Mocks:
        """A fixture that returns a Mocks instance."""
        return TestAddIdentity.Mocks(mocker)
        #

    def test_signal_exception(self, mocks: Mocks) -> None:
        """Catch SignalException."""
        mocks.expect.side_effect = SignalException(15)

        agent = SSHAgent()

        with pytest.raises(ExitCodeError) as exc_info:
            agent.add_identity("/test/fake")

        assert exc_info.value.exit_code == 130
        assert isinstance(exc_info.value.__context__, SignalException)
        mocks.sendintr.assert_called_once()
        mocks.close.assert_called_once()
        #

    def test_rethrow_exception(self, mocks: Mocks) -> None:
        """Rethrow unknown exceptions."""
        mocks.expect.side_effect = Exception("Fake")

        agent = SSHAgent()

        with pytest.raises(Exception) as exc_info:
            agent.add_identity("/test/fake")

        assert exc_info.value.args[0] == "Fake"
        mocks.isalive.assert_called_once()
        #

    def test_finally_with_isalive_false(self, mocks: Mocks) -> None:
        """Execute finally clause with isalive set to false."""
        mocks.isalive.return_value = False
        mocks.expect.side_effect = EOF("Fake")

        SSHAgent().add_identity("/test/fake")

        mocks.close.assert_called_once()  # This is into except EOF clause
        mocks.isalive.assert_called_once()  # This is into finally clause
        #

    def test_finally_with_isalive_true(self, mocks: Mocks) -> None:
        """Execute finally clause with isalive set to true."""
        mocks.isalive.return_value = True
        mocks.expect.side_effect = Exception("Fake")

        agent = SSHAgent()

        with pytest.raises(Exception):
            agent.add_identity("/test/fake")

        mocks.isalive.assert_called_once()
        mocks.close.assert_called_once()  # This is into finally clause
        #

    def test_expect_eof_with_exitstatus(self, mocks: Mocks) -> None:
        """Throw an ExitCodeError if the closed child has an non-zero exitstatus."""
        mocks.expect.side_effect = EOF("Fake")
        mocks.child.exitstatus = 42

        agent = SSHAgent()

        with pytest.raises(ExitCodeError) as exc_info:
            agent.add_identity("/test/fake")

        mocks.close.assert_called()
        assert exc_info.value.exit_code == 42
        #

    def test_expect_eof_with_signalstatus(self, mocks: Mocks) -> None:
        """Throw an SignalException if the closed child has an non-zero signalstatus."""
        mocks.expect.side_effect = EOF("Fake")
        mocks.child.signalstatus = 2

        agent = SSHAgent()

        with pytest.raises(ExitCodeError) as exc_info:
            agent.add_identity("/test/fake")

        mocks.close.assert_called()
        assert exc_info.value.exit_code == 130
        assert isinstance(exc_info.value.__context__, SignalException)
        assert cast(SignalException, exc_info.value.__context__).signal_num == 2
        #

    def test_expect_timeout(self, mocks: Mocks) -> None:
        """Throw a RuntimeError if expect throws a TIMEOUT."""
        mocks.expect.side_effect = TIMEOUT("Fake")

        agent = SSHAgent()

        with pytest.raises(RuntimeError) as exc_info:
            agent.add_identity("/test/fake")

        assert exc_info.value.args[0] == "ssh-add did not run as expected"
        assert isinstance(exc_info.value.__context__, TIMEOUT)
        assert cast(TIMEOUT, exc_info.value.__context__).args[0] == "Fake"
        #

    def test_expect_stdout_write_only(self, mocks: Mocks) -> None:
        """Write only to stdout if expect returns 2."""
        mocks.expect.side_effect = [2, EOF("Fake")]
        mocks.child.after = "fake"
        mock_stdout_write = mocks.mocker.patch("sys.stdout.write")

        SSHAgent().add_identity("/test/fake")

        mock_stdout_write.assert_called_once_with("fake")
        mocks.close.assert_called()
        #

    def test_expect_prompt_passphrare(self, mocks: Mocks) -> None:
        """Prompt for a passphrase if expect returns 0 or 1."""
        mocks.expect.side_effect = [0, EOF("Fake")]
        mocks.child.after = "Fake"
        mock_getpass = mocks.mocker.patch("getpass.getpass", return_value="fake")

        SSHAgent().add_identity("/test/fake")

        mock_getpass.assert_called_once()
        mocks.sendline.assert_called_once()
        mocks.close.assert_called()

    def test_expect_prompt_passphrare_empty(self, mocks: Mocks) -> None:
        """Send an wrong passphrase if the one returned by getpass is empty."""
        mocks.expect.side_effect = [1, EOF("Fake")]
        mocks.child.after = "Fake"
        mock_getpass = mocks.mocker.patch("getpass.getpass", return_value="")

        SSHAgent().add_identity("/test/fake")

        mock_getpass.assert_called_once()
        mocks.sendline.assert_called_once_with(">P_F&DFdbob20m5wl`e;ARviU@Lb>*(Uuw_?A~0cILXPlDU8f;")
        mocks.close.assert_called()


class TestIsIdentityStored:
    """is_identity_stored method"""  # noqa: D415

    class Mocks:
        """Some mocks for the tests."""

        def __init__(self, mocker: MockerFixture) -> None:  # noqa: D107
            self.mocker = mocker

            self.popen = mocker.patch("ssh_agent_add_id.ssh_agent.Popen")
            self.communicate: MockType = self.popen.return_value.communicate
            self.communicate.return_value = ("fake stdout", "fake stderr")
            self.poll: MockType = self.popen.return_value.poll
            self.poll.return_value = None
            self.send_signal: MockType = self.popen.return_value.send_signal
            self.terminate: MockType = self.popen.return_value.terminate
            #

    @pytest.fixture
    def mocks(self, mocker: MockerFixture) -> Mocks:
        """A fixture that returns a Mocks instance."""
        return TestIsIdentityStored.Mocks(mocker)
        #

    def test_called_process_error(self, mocks: Mocks) -> None:
        """Catch CalledProcessError."""
        mocks.communicate.side_effect = CalledProcessError(
            42, "fake_cmd", "fake stdout", "fake stderr"
        )
        mock_stdout_write = mocks.mocker.patch("sys.stdout.write")
        mock_stderr_write = mocks.mocker.patch("sys.stderr.write")

        agent = SSHAgent()

        with pytest.raises(ExitCodeError) as exc_info:
            agent.is_identity_stored("/test/fake")

        assert exc_info.value.exit_code == 42
        assert exc_info.value.command == "ssh-add -T /test/fake"

        mock_stdout_write.assert_called_once_with("fake stdout\n")
        mock_stderr_write.assert_called_once_with("fake stderr\n")

        assert isinstance(exc_info.value.__context__, CalledProcessError)
        called_process_err = cast(CalledProcessError, exc_info.value.__context__)
        assert called_process_err.returncode == 42
        assert called_process_err.cmd == "fake_cmd"
        assert called_process_err.stdout == "fake stdout"
        assert called_process_err.stderr == "fake stderr"
        #

    def test_signal_exception(self, mocks: Mocks) -> None:
        """Catch SignalException."""
        mocks.communicate.side_effect = SignalException(15)

        agent = SSHAgent()

        with pytest.raises(ExitCodeError) as exc_info:
            agent.is_identity_stored("/test/fake")

        assert exc_info.value.exit_code == 130
        assert isinstance(exc_info.value.__context__, SignalException)
        mocks.send_signal.assert_called_once_with(SIGINT)
        mocks.terminate.assert_called_once()
        #

    def test_rethrow_exception(self, mocks: Mocks) -> None:
        """Rethrow unknown exceptions."""
        mocks.communicate.side_effect = Exception("Fake")

        agent = SSHAgent()

        with pytest.raises(Exception) as exc_info:
            agent.is_identity_stored("/test/fake")

        assert exc_info.value.args[0] == "Fake"
        mocks.poll.assert_called_once()
        #

    def test_finally_with_poll_returncode(self, mocks: Mocks) -> None:
        """Execute finally clause with isalive set to false."""
        mocks.popen.return_value.returncode = 0
        mocks.poll.return_value = 0

        ret = SSHAgent().is_identity_stored("/test/fake")

        assert ret is True
        mocks.poll.assert_called_once()
        mocks.terminate.assert_not_called()
        #

    def test_finally_with_isalive_true(self, mocks: Mocks) -> None:
        """Execute finally clause with isalive set to true."""
        mocks.poll.return_value = None
        mocks.communicate.side_effect = Exception("Fake")

        agent = SSHAgent()

        with pytest.raises(Exception):
            agent.is_identity_stored("/test/fake")

        mocks.poll.assert_called_once()
        mocks.terminate.assert_called_once()
        #

    def test_identity_found(self, mocks: Mocks) -> None:
        """Print a message return true if the identity is already stored by SSH agent."""
        mocks.popen.return_value.returncode = 0
        mock_print = mocks.mocker.patch("builtins.print")

        ret = SSHAgent().is_identity_stored("/test/fake")

        mock_print.assert_called_once_with("This identity has already been added to the SSH agent.")
        assert ret is True
        #

    def test_identity_not_found(self, mocks: Mocks) -> None:
        """Return false if the identity is not stored by SSH agent."""
        mocks.popen.return_value.returncode = 1

        ret = SSHAgent().is_identity_stored("/test/fake")

        assert ret is False
        #

    def test_non_zero_returncode(self, mocks: Mocks) -> None:
        """Throw a CalledProcessError if returncode is not zero."""
        mocks.popen.return_value.returncode = 42
        mocks.popen.return_value.args = ["fake_cmd", "--test"]

        agent = SSHAgent()

        with pytest.raises(ExitCodeError) as exc_info:
            agent.is_identity_stored("/test/fake")

        assert exc_info.value.exit_code == 42
        assert exc_info.value.command == "ssh-add -T /test/fake"

        assert isinstance(exc_info.value.__context__, CalledProcessError)
        called_process_err = cast(CalledProcessError, exc_info.value.__context__)
        assert called_process_err.returncode == 42
        assert called_process_err.cmd == ["fake_cmd", "--test"]
        assert called_process_err.stdout == "fake stdout"
        assert called_process_err.stderr == "fake stderr"
        #

    def test_returncode_none(self, mocks: Mocks) -> None:
        """Throw a RuntimeError if returncode is None."""
        mocks.popen.return_value.returncode = None

        agent = SSHAgent()

        with pytest.raises(RuntimeError) as exc_info:
            agent.is_identity_stored("/test/fake")

        assert exc_info.value.args[0] == "ssh-add did not terminate as expected"
        #

    def test_negative_returncode(self, mocks: Mocks) -> None:
        """Throw a ValueError is negative or something else."""
        mocks.popen.return_value.returncode = -42

        agent = SSHAgent()

        with pytest.raises(ValueError) as exc_info:
            agent.is_identity_stored("/test/fake")

        assert exc_info.value.args[0] == "Unexpected Popen returncode value: [int] -42"
