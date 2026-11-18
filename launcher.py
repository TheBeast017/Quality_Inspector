
import os, sys
os.environ.setdefault("INSPECTION_HOME", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ["INSPECTION_HOME"])
import api.main  # noqa: F401
