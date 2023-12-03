from pathlib import Path
from typing import cast

import pytest
from pytest import CaptureFixture
from pytest_mock.plugin import MockerFixture, MockType
from ssh_agent_add_id.cli import main
from ssh_agent_add_id.errors import ExitCodeError


class TestMain:
    """main function"""  # noqa: D415

    class Mocks:
        """Some mocks for the tests."""

        def __init__(self, mocker: MockerFixture) -> None:  # noqa: D107
            self.mocker = mocker

            self.getenv = mocker.patch("os.getenv", return_value="/test/fake.socket")
            self.which = mocker.patch("shutil.which", return_value="/test/fake/ssh-add")

            self.cli_args: MockType = mocker.patch("ssh_agent_add_id.cli.CliArguments").return_value
            self.cli_args.resolve_priv_key_path.return_value = Path("/test/fake/priv")
            self.cli_args.resolve_pub_key_path.return_value = Path("/test/fake/pub")

            self.signal_handler = mocker.patch("ssh_agent_add_id.cli.SignalHandler")

            self.ssh_agent: MockType = mocker.patch("ssh_agent_add_id.cli.SSHAgent")
            self.add_identity: MockType = self.ssh_agent.return_value.add_identity
            self.is_identity_stored: MockType = self.ssh_agent.return_value.is_identity_stored
            #

    @pytest.fixture
    def mocks(self, mocker: MockerFixture) -> Mocks:
        """A fixture that returns a Mocks instance."""
        return TestMain.Mocks(mocker)
        #

    def test_ssh_add_not_found(self, mocks: Mocks, capsys: CaptureFixture) -> None:
        """Throw a FileNotFoundError if ssh-add command not found."""
        mocks.which.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.args[0] == 1
        assert capsys.readouterr().err == "ssh-add command not found\n"
        assert isinstance(exc_info.value.__context__, FileNotFoundError)
        #

    def test_ssh_auth_sock_not_found(self, mocks: Mocks, capsys: CaptureFixture) -> None:
        """Throw a ValueError if SSH_AUTH_SOCK is not defined."""
        mocks.getenv.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.args[0] == 1
        assert cast(str, capsys.readouterr().err).startswith("SSH_AUTH_SOCK not found.")
        assert isinstance(exc_info.value.__context__, ValueError)
        #

    def test_exit_code_error(self, mocks: Mocks, capsys: CaptureFixture) -> None:
        """Catch ExitCodeError."""
        mocks.ssh_agent.side_effect = ExitCodeError(42, "fake_cmd")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.args[0] == 42
        assert capsys.readouterr().err == "Command 'fake_cmd' returned exit code 42\n"
        assert isinstance(exc_info.value.__context__, ExitCodeError)
        #

    def test_is_identity_stored_true(self, mocks: Mocks) -> None:
        """Do not call add_identity when is_identity_stored returns True."""
        mocks.is_identity_stored.return_value = True

        main()

        mocks.is_identity_stored.assert_called_once()
        mocks.add_identity.assert_not_called()
        #

    def test_is_identity_stored_false(self, mocks: Mocks) -> None:
        """Call add_identity when is_identity_stored returns False."""
        mocks.is_identity_stored.return_value = False

        main()

        mocks.is_identity_stored.assert_called_once()
        mocks.add_identity.assert_called_once()
