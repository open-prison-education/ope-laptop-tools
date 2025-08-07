import sys
from pathlib import Path

# Get the absolute path to the module root directory
module_root = Path(__file__).resolve().parent

if str(module_root) not in sys.path:
	sys.path.insert(0, str(module_root))
