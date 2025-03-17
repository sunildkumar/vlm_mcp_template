import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent)) 

def pytest_configure(config):
    config.option.tbstyle = "native" 
