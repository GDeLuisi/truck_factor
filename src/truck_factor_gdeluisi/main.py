
from tempfile import gettempdir
from .helper import *
import pandas as pd

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

def _filter_files_of_interest(df:pd.DataFrame,pl_threshold=0.35):
    files=df["fname"].unique().tolist()
    exts=infer_programming_language(files,pl_threshold)
    exts=resolve_programming_languages(exts)
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

    
