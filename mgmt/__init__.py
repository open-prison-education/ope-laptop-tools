import sys
from pathlib import Path

# Get the absolute path to the project root directory
project_root = Path(__file__).resolve().parent.parent

# Add project root to Python path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
