import sys
import os
import tkinter as tk
from pathlib import Path

# Add src to path so we can resolve submodules
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui.main_window import CbzApp

def main():
    root = tk.Tk()
    app = CbzApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
