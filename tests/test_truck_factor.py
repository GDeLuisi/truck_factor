from src.truck_factor_gdeluisi.helper import *
from src.truck_factor_gdeluisi.main import *
from pytest import mark,raises
from pathlib import Path
import pandas as pd
import subprocess
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor

git_repos=[
            (Path.cwd().as_posix(),True),
            (Path.cwd().parent.as_posix(),False),
            # (Path.cwd().parent.joinpath("project_visualization_tool").as_posix(),1),
            # (Path.cwd().parent.joinpath("pandas").as_posix(),True),
            # (Path.cwd().parent.joinpath("emacs-theme-gruvbox").as_posix(),True)
        ]
@mark.parametrize("path,expected",git_repos)
def test_contribution_df(path,expected):
    if expected:
        current_files=set(subprocess.check_output(f"git -C {path} ls-files",shell=True).decode()[:-1].split('\n'))
        df=create_contribution_dataframe(path)
        df.info()
        assert set(df["fname"].to_list()).issubset(current_files)
    else:
        with raises(Exception):
            create_contribution_dataframe(path)

@mark.parametrize("path,expected",git_repos)
def test_compute_tf(path,expected):
    if expected:
        tf=compute_truck_factor(path)
        print(tf)
    else:
        with raises(Exception):
            compute_truck_factor(path)