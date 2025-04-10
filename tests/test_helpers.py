from src.truck_factor_gdeluisi.helper import write_logs,is_git_available,get_head_commit
from pytest import mark,raises
from pathlib import Path

git_repos=[
                     (Path.cwd().as_posix(),True),
                     (Path.cwd().parent.as_posix(),False)
                 ]

@mark.parametrize("path,expected",git_repos)
def test_write_logs(path,expected):
    if expected:
        write_logs(path,"HEAD")
        assert True
    else:
        with raises(Exception):
            write_logs(path,"HEAD")

def test_is_git_available():
    
    assert is_git_available()
        

@mark.parametrize("path,expected",git_repos)
def test_get_head_commit(path,expected):
    if expected:
        get_head_commit(path)
        assert True
    else:
        with raises(Exception):
            get_head_commit(path)

@mark.parametrize("path,expected",git_repos)
def test_write_logs_integration(path,expected):
    if expected:
        write_logs(path)
        assert True
    else:
        with raises(Exception):
            write_logs(path)