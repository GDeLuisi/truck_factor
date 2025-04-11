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
        cmds.append(_cmd_builder("log",repo,head,r'format:%h|%an|%ad',False,c_slice,i*c_slice,"--date=short","--num-stat","--all"))
    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        worker=partial(subprocess.check_output,shell=True)
        results=executor.map(worker,cmds)
    return "\n".join([r.decode() for r in results])

#TODO: factorize for command specific
def _cmd_builder(command:str,repo:str,commit:Optional[str]=None,pretty:Optional[str]=None,merges:bool=False,max_count:Optional[int]=None,skip:Optional[int]=None,*args):
    arg_string=f"git -C {repo} {command} "
    if not commit:
        commit=get_head_commit()
    arg_string=arg_string + commit
    arg_list=[command]
    if max_count!=None:
        arg_list.append(f"--max-count={max_count}")
    if skip!=None:
        arg_list.append(f"--max-count={skip}")
    if merges:
        arg_list.append("--no-merges")
    if pretty!=None:
        arg_list.append(f'--pretty="format:{pretty}"')
    arg_string=arg_string + " "+ " ".join(arg_list) + " " +" ".join(args)
    return arg_string

def clear_files_aliases():
    pass

def count_commits(path:str,commit_sha:Optional[str]=None)->int:
    repo=Path(path).resolve().as_posix()
    head=commit_sha
    if not commit_sha:
        head=get_head_commit(path)
    
    cmd=f"git -C {repo} rev-list {head} --count --all --no-merges"
    
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