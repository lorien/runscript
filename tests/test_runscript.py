from subprocess import CalledProcessError, check_output  # nosec B404

import pytest


def test_simple_script():
    out = check_output("cd tests; run demo", shell=True)  # nosec B602, B607
    assert out.rstrip() == b"demo output"


def test_error_exit_code():
    def fail():
        check_output("cd tests; run error", shell=True)  # nosec B602, B607

    with pytest.raises(CalledProcessError):
        fail()

    try:
        fail()
    except CalledProcessError as ex:
        assert ex.returncode == 1
