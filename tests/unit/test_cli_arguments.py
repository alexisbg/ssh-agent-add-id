from pathlib import Path
import sys

import pytest
from pytest import CaptureFixture
from pytest_mock.plugin import MockerFixture
from ssh_agent_add_id.cli_arguments import CliArguments


PROG = "ssh-agent-add-id"


def init_cli_args() -> CliArguments:
    """Initialize a CliArguments instance."""
    sys.argv = [PROG, "/test/fake"]
    return CliArguments()


class TestInit:
    """__init__ method"""  # noqa: D415

    def test_wrong_arg(self, capsys: CaptureFixture) -> None:
        """Throw a SystemExit error if there is an unrecognized argument."""
        sys.argv = [PROG, "/test/fake", "/test/fake.pub", "extra_arg"]

        with pytest.raises(SystemExit) as exc_info:
            CliArguments()

        assert exc_info.value.args[0] == 2
        assert "unrecognized arguments: extra_arg" in capsys.readouterr().err
        #

    def test_priv_key_path_arg(self) -> None:
        """Handle priv_key_path positional argument."""
        sys.argv = [PROG, "/test/fake"]

        args = CliArguments()

        assert args._args.priv_key_path == "/test/fake"
        assert args._args.pub_key_path is None
        #

    def test_pub_key_path_arg(self) -> None:
        """Handle priv_key_path positional argument."""
        sys.argv = [PROG, "/test/fake", "/test/fake.pub"]

        args = CliArguments()

        assert args._args.priv_key_path == "/test/fake"
        assert args._args.pub_key_path == "/test/fake.pub"


class TestResolvePrivKeyPath:
    """resolve_priv_key_path method"""  # noqa: D415

    def test_defined_priv_key_path(self, mocker: MockerFixture) -> None:
        """Return _priv_key_path if it is already defined."""
        mock_expanduser = mocker.patch.object(Path, "expanduser")

        args = init_cli_args()
        args._priv_key_path = Path("/test/fake/again")

        assert str(args.resolve_priv_key_path()) == "/test/fake/again"
        mock_expanduser.assert_not_called()
        #

    def test_file_not_found(self, mocker: MockerFixture) -> None:
        """Throw FileNotFoundError if the resolved key path does not exist."""
        mocker.patch.object(Path, "resolve", return_value=Path("/test/fake/resolve"))
        mocker.patch.object(Path, "exists", return_value=False)

        args = init_cli_args()

        with pytest.raises(FileNotFoundError) as exc_info:
            args.resolve_priv_key_path()

        assert exc_info.value.args[0] == "/test/fake/resolve not found"
        #

    def test_success(self, mocker: MockerFixture) -> None:
        """Run as expected."""
        mocker.patch.object(Path, "resolve", return_value=Path("/test/fake/success"))
        mocker.patch.object(Path, "exists", return_value=True)

        args = init_cli_args()
        args.resolve_priv_key_path()

        assert str(args.resolve_priv_key_path()) == "/test/fake/success"


class TestResolvePubKeyPath:
    """resolve_pub_key_path method"""  # noqa: D415

    def test_defined_pub_key_path_attr(self, mocker: MockerFixture) -> None:
        """Return _pub_key_path if it is already defined."""
        mock_expanduser = mocker.patch.object(Path, "expanduser")

        args = init_cli_args()
        args._pub_key_path = Path("/test/fake.pub")

        assert str(args.resolve_pub_key_path()) == "/test/fake.pub"
        mock_expanduser.assert_not_called()
        #

    def test_with_pub_key_path_arg(self, mocker: MockerFixture) -> None:
        """Use pub_key_path argument if passed."""
        PUB_KEY_PATH = "/test/fake/resolve_pub"
        mock_resolve = mocker.patch.object(Path, "resolve", return_value=Path(PUB_KEY_PATH))
        mocker.patch.object(Path, "exists", return_value=True)

        args = init_cli_args()
        args._args.pub_key_path = PUB_KEY_PATH

        assert str(args.resolve_pub_key_path()) == PUB_KEY_PATH
        mock_resolve.assert_called_once()
        #

    def test_concat_pub_ext(self, mocker: MockerFixture) -> None:
        """Concatenate .pub to _priv_key_path if pub_key_path argument is not passed."""
        mocker.patch.object(Path, "exists", return_value=True)

        args = init_cli_args()
        args._priv_key_path = Path("/test/fake")

        assert str(args.resolve_pub_key_path()) == "/test/fake.pub"
        #

    def test_resolve_priv_key_path(self, mocker: MockerFixture) -> None:
        """Call resolve_priv_key_path if _priv_key_path is not defined."""
        mock_resolve = mocker.patch.object(
            CliArguments, "resolve_priv_key_path", return_value=Path("/test/fake")
        )
        mocker.patch.object(Path, "exists", return_value=True)

        args = init_cli_args()

        assert str(args.resolve_pub_key_path()) == "/test/fake.pub"
        mock_resolve.assert_called_once()
        #

    def test_file_not_found(self, mocker: MockerFixture) -> None:
        """Throw FileNotFoundError if the resolved key path does not exist."""
        mocker.patch.object(Path, "exists", return_value=False)

        args = init_cli_args()
        args._priv_key_path = Path("/test/fake")

        with pytest.raises(FileNotFoundError) as exc_info:
            args.resolve_pub_key_path()

        assert exc_info.value.args[0] == "/test/fake.pub not found"
