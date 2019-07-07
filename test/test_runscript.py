from subprocess import check_output, check_call, CalledProcessError

import pytest


def test_simple_script():
    out = check_output('cd test; run foo', shell=True)
    assert out.rstrip() == b'foo foo'


def test_error_exit_code():
    def fail():
        check_output('cd test; run error', shell=True)

    with pytest.raises(CalledProcessError):
        fail()

    try:
        fail()
    except CalledProcessError as ex:
        assert ex.returncode == 1
