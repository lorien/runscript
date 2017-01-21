from subprocess import check_output


def test_simple_script():
    out = check_output('cd test; run foo', shell=True)
    assert out.rstrip() == b'foo foo'
