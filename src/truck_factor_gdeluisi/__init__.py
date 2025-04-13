from importlib.metadata import version
try:
    __version__=version(__package__) 
except Exception:
    __version__="not available"