from src.truck_factor_gdeluisi.helper import *
from pytest import mark,raises
from pathlib import Path
import pandas as pd
from logging import getLogger
import subprocess
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor

git_repos=[
            (Path.cwd().as_posix(),True),
            (Path.cwd().parent.as_posix(),False),
            # (Path.cwd().parent.joinpath("project_visualization_tool").as_posix(),True),
            # (Path.cwd().parent.joinpath("pandas").as_posix(),True),
            # (Path.cwd().parent.joinpath("emacs-theme-gruvbox").as_posix(),True)
        ]

logger=getLogger()
@mark.parametrize("path,expected",git_repos)
def test_write_logs(path,expected):
    if expected:
        with open("./write_logs.txt","w",encoding="utf-8") as f:
            print(write_logs(path,"HEAD"),file=f)
        assert True
    else:
        with raises(Exception):
            write_logs(path,"HEAD")
            
@mark.parametrize("path,expected",git_repos)
def test_get_aliases(path,expected):
    if expected:
        current_files=set(subprocess.check_output(f"git -C {path} ls-files",shell=True).decode()[:-1].split('\n'))
        alias_map_values=set(get_aliases(path,"HEAD").values())
        print(current_files)
        print("#############################################")
        print(alias_map_values)
        assert alias_map_values.issubset(current_files)
    else:
        with raises(Exception):
            get_aliases(path,"HEAD")
            
@mark.parametrize("iterable,n,expected",[
    (list(range(150000)),10,True),
    ([],10,False),
    (list(range(150000)),0,False),
    (list(range(150000)),None,False),
    (None,10,False),
])
def test_create_batches(iterable,n,expected):
    if expected:
        tmp=list(iterable)
        n_batches=ceil(len(tmp)/n)
        batches=create_batches(iterable,n)
        assert n_batches==len(batches)
        rec_iterable=[]
        for b in batches:
            rec_iterable.extend(b)
        assert sorted(tmp)==sorted(rec_iterable)
    else:
        with raises(ValueError):
            create_batches(iterable,n)
            
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
            


@mark.parametrize("path,expected",git_repos)
def test_write_logs_parallel(path,expected):
    if expected:
        res=write_logs(path)
        res=res.split("\n\n")
        print(len(res))
        with open("./test_logs.txt","w",encoding="utf-8") as f:
            print(res,file=f)
    else:
        with raises(Exception):
            write_logs(path)
            
def test_infer_programming_language():
    files=[
    ".github/workflows/publist_pypi.yml",
    ".github/workflows/tag_on_merge.yaml",
    ".github/workflows/test-dev.yml",
    ".github/workflows/testpypi_publish.yml",
    ".gitignore",
    ".python-version",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "src/truck_factor_gdeluisi/__init__.py",
    "src/truck_factor_gdeluisi/helper.py",
    "src/truck_factor_gdeluisi/main.py",
    "tests/__init__.py",
    "tests/test_helpers.py"
    ]
    exts=infer_programming_language(files=files)
    exts=resolve_programming_languages(exts)
    assert exts=={".py"}

@mark.parametrize("path,expected",git_repos)
def test_parse_logs(path,expected):
    # commit="0cb8f542538a6a53c8646da7d171e5bfec40ac1a"
    if expected:
        commit="HEAD"
        res_df=parse_logs(write_logs(path,commit))
        # res_df=parse_logs(write_logs(Path.cwd().parent.joinpath("pandas").as_posix(),commit))
        
        with open("./test_logs.json","w",encoding="utf-8") as f:
            print(res_df,file=f)
        assert True
        
    else:
        with raises(Exception):
            parse_logs(write_logs(Path.cwd().as_posix(),commit))
            