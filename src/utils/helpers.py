import logging
import os
import sys
import datetime
from pathlib import Path

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In development, resolve from the src root
        # This assumes helpers.py is in src/utils/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

# Configure logging
def setup_logging(ui_handler=None):
    """
    Sets up the logging configuration.
    If ui_handler is provided, adds it to the logger.
    """
    logger = logging.getLogger("CBZMaster")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

    # Stream Handler (Console)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # UI Handler (if provided, e.g., for Tkinter Text widget)
    if ui_handler:
        ui_handler.setLevel(logging.INFO)
        ui_handler.setFormatter(formatter)
        logger.addHandler(ui_handler)
    
    return logger

def send_to_recycle_bin(path):
    """
    Sends a file or directory to the Windows Recycle Bin using PowerShell.
    This avoids external dependencies like send2trash or winshell.
    """
    import subprocess
    
    # PowerShell command to use VisualBasic's FileSystem.DeleteFile/DeleteDirectory
    # "Microsoft.VisualBasic.FileIO.FileSystem" provides a method to send to Recycle Bin.
    # UIOption.OnlyErrorDialogs = 2, RecycleOption.SendToRecycleBin = 2
    
    abspath = os.path.abspath(path)
    
    # Escape single quotes for PowerShell
    ps_path = f"'{abspath.replace("'", "''")}'"
    
    # We detect if it's file or dir to call appropriate method
    if os.path.isdir(abspath):
        cmd = f"""
        Add-Type -AssemblyName Microsoft.VisualBasic
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory({ps_path}, 'OnlyErrorDialogs', 'SendToRecycleBin')
        """
    else:
        cmd = f"""
        Add-Type -AssemblyName Microsoft.VisualBasic
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile({ps_path}, 'OnlyErrorDialogs', 'SendToRecycleBin')
        """
        
    try:
        # Run PowerShell command
        subprocess.run(["powershell", "-Command", cmd], check=True, capture_output=True)
        return True, "Recycled"
    except subprocess.CalledProcessError as e:
        return False, f"PowerShell Error: {e.stderr.decode()}"
    except Exception as e:
        return False, str(e)

logger = setup_logging()
