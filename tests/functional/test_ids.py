import os
import re
import subprocess
from subprocess import STDOUT, CalledProcessError
import sys
from typing import Dict, Iterator, List, cast

from pexpect import EOF
import pytest
from pytest import CaptureFixture
from pytest_mock import MockerFixture
from ssh_agent_add_id.cli import main
from ssh_agent_add_id.constants import APP_NAME
from ssh_agent_add_id.errors import ExitCodeError


PREFIX = "tests/functional/ids/"
PRIV_KEYS: List[str] = [
    "id_dsa",
    "id_ecdsa_256",
    "id_ecdsa_384",
    "id_ecdsa_521",
    "id_ed25519",
    "id_ed25519_no_pswd",
    "id_rsa_b1024",
    "pkcs8.pem",
]
PUB_KEYS: Dict[str, str] = {"pkcs8.pem": "pkcs8.pub"}


@pytest.fixture(scope="module", autouse=True)
def setup_teardown() -> Iterator[None]:
    """Remove all identities from the SSH agent before and after all test methods."""
    subprocess.check_call(["ssh-add", "-D"])

    yield None

    if not os.getenv("TEST_UUID"):  # Tests are not running with VS Code
        subprocess.check_call(["ssh-add", "-D"], stderr=STDOUT)


def test_invalid_public_key(capsys: CaptureFixture) -> None:
    """Return an error if public key is invalid."""
    sys.argv = [
        APP_NAME,
        PREFIX + "putty_ed25519.ppk",
        PREFIX + "putty_ed25519_ssh2.pub",
    ]

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    assert isinstance(exc_info.value.__context__, ExitCodeError)
    exit_code_error = cast(ExitCodeError, exc_info.value.__context__)
    assert exit_code_error.exit_code == 1
    assert exit_code_error.command and exit_code_error.command.startswith("ssh-add -T")

    assert isinstance(exit_code_error.__context__, CalledProcessError)
    process_error = cast(CalledProcessError, exit_code_error.__context__)
    assert process_error.returncode == 1
    assert "ssh-add" in process_error.cmd and "-T" in process_error.cmd

    out: List[str] = cast(str, capsys.readouterr().err).split("\r\n")
    assert len(out) == 2
    assert out[0].startswith("Couldn't read public key")
    assert out[1].endswith("returned exit code 1\n")


def test_invalid_private_key(capsys: CaptureFixture) -> None:
    """Return an error if private key is invalid."""
    sys.argv = [
        APP_NAME,
        PREFIX + "putty_ed25519.ppk",
        PREFIX + "putty_ed25519_openssh.pub",
    ]

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    assert isinstance(exc_info.value.__context__, ExitCodeError)
    exit_code_error = cast(ExitCodeError, exc_info.value.__context__)
    assert exit_code_error.exit_code == 1
    assert exit_code_error.command and exit_code_error.command.startswith("ssh-add")
    assert isinstance(exit_code_error.__context__, EOF)

    out: List[str] = cast(str, capsys.readouterr().err).split("\r\n")
    assert len(out) == 2
    assert re.match(r"^Error loading key.+invalid format$", out[0])
    assert out[1].endswith("returned exit code 1\n")


@pytest.mark.parametrize("key", PRIV_KEYS)
def test_add_new_id(key: str, mocker: MockerFixture, capsys: CaptureFixture) -> None:
    """Add an identity ti SSH agent if it is not already stored."""
    mocker.patch("getpass.getpass", return_value="fake")

    sys.argv = [APP_NAME, PREFIX + key]
    if key in PUB_KEYS:
        sys.argv.append(PREFIX + PUB_KEYS[key])

    main()

    assert "Identity added: " in capsys.readouterr().out


@pytest.mark.after_test("test_add_new_id")
@pytest.mark.parametrize("key", PRIV_KEYS)
def test_stored_id(key: str, capsys: CaptureFixture) -> None:
    """Test."""
    sys.argv = [APP_NAME, PREFIX + key]
    if key in PUB_KEYS:
        sys.argv.append(PREFIX + PUB_KEYS[key])

    main()

    assert "This identity has already been added to the SSH agent." in capsys.readouterr().out
