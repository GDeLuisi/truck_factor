
from tempfile import gettempdir
from .helper import *
import pandas as pd
from math import log1p
def _resolve_aliases(df:pd.DataFrame,aliases:dict)->pd.DataFrame:
    new_df=df
    # new_df.info()
    # print(new_df["fname"].head())
    for alias,value in aliases.items():
        try:
            new_df.replace({"fname":alias},value,inplace=True)
        except KeyError:
            continue
    return new_df

def _filter_dead_files(df:pd.DataFrame,current_files:Iterable[str])->pd.DataFrame:
    new_df=df.loc[df["fname"].isin(current_files)]
    return new_df

def _filter_files_of_interest(df:pd.DataFrame):
    files=df["fname"].unique()
    exts=infer_programming_language(files)
    # print(exts)
    exts=resolve_programming_languages(exts)
    # print(exts)
    tmp_df=df.copy()
    tmp_df["ext"]=df["fname"].apply(lambda f: "."+f.rsplit(".",1)[1] if len(f.rsplit(".",1))>1 else "")
    tmp_df=tmp_df.loc[tmp_df["ext"].isin(exts)]
    tmp_df.reset_index(drop=True,inplace=True)
    return tmp_df

def create_contribution_dataframe(repo:str)->pd.DataFrame:
    contributions=parse_logs(write_logs(repo))
    df=pd.DataFrame(contributions)
    df["date"]=pd.to_datetime(df["date"])
    alias_map=get_aliases(repo)
    df=_resolve_aliases(df,alias_map)
    current_files=set(subprocess.check_output(f"git -C {repo} ls-files",shell=True).decode()[:-1].split('\n'))
    df=_filter_dead_files(df,current_files)
    df=_filter_files_of_interest(df)
    df.sort_values("date",inplace=True)
    return df

def _compute_DOA(row:pd.Series,kwargs:dict):
    files_fa=kwargs["files_fa"]
    files_contr=kwargs["files_contr"]
    fname=row["fname"]
    FA=1 if files_fa[fname] == row["author"] else 0
    DL=row["tot_contributions"]
    AC=files_contr[fname] - DL
    DOA=3.293 + 1.098 *  FA + 0.164* DL - 0.321 *  log1p(AC)
    return DOA

def compute_DOA(contributions:pd.DataFrame)->pd.DataFrame:
    if contributions.empty:
        return contributions
    #DOA=3.293 + 1.098 × FA(md, fp) + 0.164×DL(md, fp) − 0.321 × ln(1 + AC (md, fp))
    df=contributions.groupby(["fname","author","date"]).sum().reset_index(drop=False)
    #drop all 0 contributions
    df=df.loc[df["tot_contributions"]!=0]
    df["DOA"]=0
    tracked_files=df["fname"].unique()
    per_author_df=df.groupby(["fname","author"]).sum(True).reset_index(drop=False)
    per_file_df=per_author_df.groupby(["fname"]).sum(True).reset_index(drop=False)
    files_contr:dict[str,int]=dict()
    files_fa:dict[str,str]=dict()
    for f in tracked_files:
        author=df.loc[df["fname"]==f]["author"].iloc[0]
        files_fa[f]=author
        files_contr[f]=per_file_df.loc[per_file_df["fname"]==f]["tot_contributions"].iloc[0]
    per_author_df["DOA"]=per_author_df.apply(_compute_DOA,axis=1,kwargs=dict(files_fa=files_fa,files_contr=files_contr))
    for f in tracked_files:
        max_doa=per_author_df.loc[per_author_df["fname"]==f]["DOA"].max()
        mask=per_author_df["fname"].eq(f)
        normalized_doas=per_author_df.loc[per_author_df["fname"]==f]["DOA"].apply(lambda v: v/max_doa)
        per_author_df.loc[mask,"DOA"]=normalized_doas
    return per_author_df


def compute_truck_factor(repo:str,orphan_files_threashold:float=0.5,authorship_threshold:float=0.7)->int:
    if not( (orphan_files_threashold >0 and orphan_files_threashold <=1 ) and (authorship_threshold >0 and authorship_threshold <=1 )):
        raise ValueError("All threshold values must have a value between 0 and 1")
    #https://arxiv.org/abs/1604.06766
    if not is_git_available():
        raise Exception("No git CLI found on PATH")
    if not is_dir_a_repo(repo):
        raise ValueError(f"Path {repo} is not a git directory")
    df=create_contribution_dataframe(repo)
    if df.empty:
        raise ValueError("Repository not suited for truck factor calculation, no source code found")
    df=compute_DOA(df)
    df=df.loc[df["DOA"]>=authorship_threshold]
    orig_size=len(df["fname"].unique())
    quorum=orig_size*orphan_files_threashold
    per_author_files=pd.DataFrame()
    tmp_df=df.groupby("author").count().reset_index(drop=False)
    per_author_files["author"]=tmp_df["author"]
    per_author_files["fname"]=tmp_df["fname"]
    per_author_files.sort_values("fname",ascending=False,inplace=True)
    tf=0
    for row in per_author_files.itertuples(index=False,name="Author"):
        author=row.author
        df=df.loc[df["author"]!=author]
        tf+=1
        if len(df["fname"].unique())<=quorum:
            break
    return tf
