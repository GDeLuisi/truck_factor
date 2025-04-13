from pathlib import Path
from shutil import which
import sys
import os
import subprocess
from typing import Optional
import pandas as pd
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from math import floor,ceil
from functools import partial
from typing import Iterable
import json
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
    c_slice=ceil(no_commits/max_worker)
    cmds=[]
    for i in range(max_worker):
        cmds.append(_log_builder(repo,head,r'%an|%ad',False,c_slice,i*c_slice,None,None,"--date=short","--numstat","--all"))
    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        worker=partial(subprocess.check_output,shell=True)
        results=executor.map(worker,cmds)
    return "\n".join([r.decode() for r in results])

def get_aliases(path:str,commit_sha:Optional[str]=None)->dict[str]:
    # git log --diff-filter=R --name-status --pretty=format:
    repo=Path(path).resolve().as_posix()
    head=commit_sha
    if not commit_sha:
        head=get_head_commit(path)
    no_commits=count_commits(repo,head)
    c_slice=ceil(no_commits/max_worker)
    cmds=[]
    alias_map=dict()
    current_files=set(subprocess.check_output(_cmd_builder("ls-files",repo=repo),shell=True).decode()[:-1].split('\n'))
    for i in range(max_worker):
        cmds.append(_log_builder(repo,head,'',False,c_slice,i*c_slice,None,None,"--name-status","--all","--diff-filter=R"))
    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        worker=partial(subprocess.check_output,shell=True)
        results=executor.map(worker,cmds)
    blocks:list[str]=[]
    for res in results:
        b=res.decode().split("\n\n")
        for l_block in b:
            lines=l_block.split("\n")
            blocks.extend(lines)
    for b in blocks:
        if b=="":
            continue
        try:
            _,old,new=b.split("\t")
            alias_map[old]=new.strip("\n")
        except ValueError:
            # print([b])
            return dict()
    final_alias_map=dict()
    for k,v in alias_map.items():
        if v in alias_map:
            #reconstruct reference chain
            to_add={k}
            tmp_v=v
            while tmp_v not in current_files:
                to_add.add(tmp_v)
                try:
                    tmp_v=alias_map[tmp_v]
                    if tmp_v in to_add:
                        raise KeyError()
                except KeyError:
                    to_add=set()
                    break
            final_v=tmp_v
            for k_v in to_add:
                final_alias_map[k_v]=final_v
        elif v in current_files:
            final_alias_map[k]=v

    return final_alias_map
        
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
        arg_list.append(f"--skip={skip}")
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

def create_batches(it:Iterable,n:int)->Iterable[Iterable]:
    if not n:
        raise ValueError("n must be at least 1")
    if not it:
        raise ValueError("Iterable cannot be None or empty")
    batches=[]
    tmp=list(it)
    n_items=len(tmp)
    if n_items==0:
        raise ValueError("Iterable must not be empty")
    n_batches=ceil(n_items/n)
    for i in range(0,n_items,n):
        batches.append(tmp[i:i+n])
    return tuple(batches)

def parse_block(block:str)->list[dict[str]]:
    contributions=dict()
    tmp=block.strip("\n").split("\n",1)
    if len(tmp)<=1:
        return []
    c_line,stat_block=tmp
    author,date=c_line.split("|")
    block_lines=stat_block.split("\n")
    contributions=[]
    for line in block_lines:
        try:
            inserted,deleted,fname=line.split('\t')
            inserted=int(inserted) if inserted!="-" else 0 
            deleted=int(deleted) if deleted!="-" else 0 
            contributions.append(dict(author=author,date=date,fname=fname,inserted=inserted,deleted=deleted,tot_contributions=inserted+deleted))
        except ValueError:
            continue
    return contributions

def _parse_logs(blocks:list[str])->list[str]:
    contr=[]
    for block in blocks:
        contr.extend(parse_block(block))
    return contr

def parse_logs(logs:str)->list[dict[str]]:
    contributions=[]
    blocks=logs.split('\n\n')
    batches=create_batches(blocks,ceil(len(blocks)/max_worker))
    with ThreadPoolExecutor(max_worker) as executor:
        results=executor.map(_parse_logs,batches)
    for r in results:
        contributions.extend(r)
    return contributions

def infer_programming_language(files:Iterable[str])->set[str]:
        fs=set(files)
        ret_suffixes=set()
        for file in fs:
            try:
                suffix=file.rsplit(".",maxsplit=1)[1]
                ret_suffixes.add("." +suffix)
            except IndexError:
                pass
        return ret_suffixes

def resolve_programming_languages(exts:Iterable[str])->set[str]:
    config_file=Path(__file__).parent.joinpath("data","ext.json")
    with config_file.open("r") as f:
        config=json.load(f)
    return {ext for ext in exts if ext in config}