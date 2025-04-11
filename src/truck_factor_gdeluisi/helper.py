from pathlib import Path
from shutil import which
import sys
import os
import subprocess
from typing import Optional
import pandas as pd
import itertools
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from math import floor
from functools import partial
max_worker = min(32,os.cpu_count())
def write_logs(path:str,commit_sha:Optional[str]=None)->str:
    """Generates formatted logs

    Args:
        path (str): path to git directory
        commit_sha (Optional[str], optional): Commit's hash value. Defaults to None.

    Returns:
        str: raw logs as strings (contains control characters)
    """
    repo=Path(path).resolve().as_posix()
    head=commit_sha
    if not commit_sha:
        head=get_head_commit(path)
    no_commits=count_commits(repo,head)
    c_slice=floor(no_commits/max_worker)
    cmds=[]
    for i in range(max_worker):
        cmds.append(_log_builder(repo,head,r'format:%h|%an|%ad',False,c_slice,i*c_slice,None,None,"--date=short","--numstat","--all"))
    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        worker=partial(subprocess.check_output,shell=True)
        results=executor.map(worker,cmds)
    return "\n".join([r.decode() for r in results])

def _cmd_builder(command:str,repo:str,*args)->str:
    """Base git command generator

    Args:
        command (str): command to use
        repo (str): git directory to execute the command on

    Returns:
        str: The complete command as a string
    """
    arg_string=f"git -C {repo} {command}"
    arg_string=arg_string + " "+ " ".join(args)
    return arg_string

def _log_builder(repo:str,commit:str,pretty:Optional[str]=None,merges:bool=False,max_count:Optional[int]=None,skip:Optional[int]=None,author:Optional[str]=None,follow:Optional[str]=None,*args)->str:
    """Builds the complete command string for a log command

    Args:
        repo (str): Git repository to execute the command on
        commit (str): The commit from which start the logging operation
        pretty (Optional[str], optional): The format used by --pretty. Defaults to None.
        merges (bool, optional): Specifies whether load merge commits. Defaults to False.
        max_count (Optional[int], optional): Paramenter for --max-count flag. Defaults to None.
        skip (Optional[int], optional): Parameter  for --skip flag. Defaults to None.
        author (Optional[str], optional): Filter only commits coming authored by the passed author. Defaults to None.
        follow (Optional[str], optional): Filter only commits which changed the passed file. Defaults to None.

    Returns:
        str: Returns the git command string
    """
    arg_list=[commit]
    if max_count!=None:
        arg_list.append(f"--max-count={max_count}")
    if skip!=None:
        arg_list.append(f"--max-count={skip}")
    if merges:
        arg_list.append("--no-merges")
    if pretty!=None:
        arg_list.append(f'--pretty="format:{pretty}"')
    if author!=None:
        arg_list.append(f'--author="{author}"')
    arg_list.extend(args)
    if follow!=None:
        arg_list.append(f'--follow -- "{follow}"')
    return _cmd_builder("log",repo,*arg_list)

def clear_files_aliases():
    pass

def count_commits(path:str,commit_sha:Optional[str]=None)->int:
    """Counts all commits reachable from a certain revision (merges excluded)

    Args:
        path (str): Path to git repository
        commit_sha (Optional[str], optional): Commit's hash value. Defaults to None.

    Returns:
        int: number of revisions counted'
    """
    repo=Path(path).resolve().as_posix()
    head=commit_sha
    if not commit_sha:
        head=get_head_commit(path)
    cmd=_cmd_builder("rev-list",repo,head, "--count", "--all" ,"--no-merges")
    return int(subprocess.check_output(cmd,shell=True).decode()[:-1])
    

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

def parse_block(block:str,exts:Optional[set[str]]=None)->dict:
    #GeggeDL|2025-04-10\n174\t0\t.gitignore\n21\t0\tLICENSE\n1\t0\tREADME.md
    contributions=dict()
    author,stat_block=block.split("\n",1)
    block_lines=stat_block.split("\n")
    contributions[author]=dict(inserted=0,deleted=0)
    for line in block_lines:
        inserted,deleted,fname=line.split('\t')
        f_split=fname.rsplit(".",1)
        if len(f_split)==2 and f_split[1] in exts:
            contributions[author]["inserted"]+=int(inserted)
            contributions[author]["deleted"]+=int(deleted)
        
def parse_logs(logs:str)->pd.DataFrame:
    #d60e612|GDeLuisi|2025-04-10
    # 1       2       src/truck_factor_gdeluisi/__init__.py
    # 55      0       src/truck_factor_gdeluisi/helper.py
    blocks=logs.split('\n\n')
    
    

def infer_programming_language(files:list[str])->set[str]:
    pass