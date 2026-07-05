import os
import sys

# make repo-root modules (tracker, categories, build_dashboard) importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
