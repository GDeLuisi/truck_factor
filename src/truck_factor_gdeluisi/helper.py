from pathlib import Path
from shutil import which
import sys
import os
import subprocess
from typing import Optional

def write_logs(path:str,commit_sha:Optional[str]=None)->str:
    repo=Path(path).resolve().as_posix()
    head=commit_sha
    if not commit_sha:
        head=get_head_commit(path)
    cmd =(
        f'git -C {repo} log {head}',
        r'--pretty=format:"\"%h\",\"%an\",\"%ad\""',
        '--date=short --numstat'
    )
    return subprocess.check_output(" ".join(cmd),shell=True).decode()[:-1]


def is_git_available()->bool:
    """Checks whether git is on PATH

    Returns:
        bool: If git is on PATH
    """
    return which("git")!=None

def is_dir_a_repo(path:str)->bool:
    """Checks whether the path points to a git directory

    Args:
        path (str): path to repo dir

    Returns:
        bool: Returns wheter the directory is a repo
    """
    cmd = f"git -C {Path(path).resolve().as_posix()} rev-parse HEAD"
    try:
        subprocess.check_call(cmd,shell=True)
        return True
    except ChildProcessError:
        return False

def get_head_commit(path:str)->str:
    """Return head commit

    Args:
        path (str): path to git directory

    Returns:
        str: Returns HEAD's commit sha
    """
    cmd = f"git -C {Path(path).resolve().as_posix()} rev-parse HEAD"
    return subprocess.check_output(cmd,shell=True).decode()[:-1]