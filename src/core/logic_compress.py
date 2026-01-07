import os
import shutil
import zipfile
from pathlib import Path
from utils.helpers import logger
import utils.helpers as utils

VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff', '.bmp'}

def is_valid_image(filename):
    return Path(filename).suffix.lower() in VALID_EXTENSIONS

def validate_folder(folder_path):
    """
    Checks if a folder is valid for CBZ conversion.
    Returns: (bool, str) -> (is_valid, reason)
    Rules:
    - Must contain at least one image.
    - Must NOT contain subdirectories.
    """
    path = Path(folder_path)
    if not path.is_dir():
        return False, "Not a directory"

    has_images = False
    
    # Check for subdirectories and images
    try:
        for entry in os.scandir(path):
            if entry.is_dir():
                 # Ignore hidden folders if necessary, but strictly no subfolders is safer request
                 return False, f"Contains subfolder: {entry.name}"
            if entry.is_file() and is_valid_image(entry.name):
                has_images = True
                
        if not has_images:
            return False, "No valid images found"
            
        return True, "OK"
    except Exception as e:
        return False, f"Access error: {e}"

def analyze_folders(source_folder):
    """
    Scans source_folder for subdirectories.
    Returns a list of items:
    [{
      'id': 'unique_id',
      'path': 'full_path',
      'name': 'folder_name',
      'orig_size': int,
      'valid': bool,
      'reason': str
    }]
    """
    items = []
    source_path = Path(source_folder)
    
    if not source_path.is_dir():
        return items

    try:
        # Sort for consistent order
        dirs = sorted([d for d in os.scandir(source_path) if d.is_dir()], key=lambda e: e.name)
        for i, d in enumerate(dirs):
            if d.name == "TO_DELETE": continue
            
            is_valid, reason = validate_folder(d.path)
            orig_size = 0
            
            if is_valid:
                # Calculate size for valid folders
                count = 0
                try:
                    for entry in os.scandir(d.path):
                        if entry.is_file() and is_valid_image(entry.name):
                            orig_size += entry.stat().st_size
                            count += 1
                except: pass
                
                # ESTIMATE 95% ratio for simple deflation
                est_final = int(orig_size * 0.95)
                pct = -5
                
                # We return keys for the GUI to translate
                status_key = "status_size_est"
                status_args = (format_bytes(orig_size), format_bytes(est_final), pct)
                reason = "Ready" # Fallback/internal
            else:
                 status_key = "status_invalid"
                 status_args = (reason,)
            
            items.append({
                'id': f"m1_{i}",
                'path': d.path,
                'name': d.name,
                'orig_size': orig_size,
                'valid': is_valid,
                'reason': reason, # Keep for debug/fallback
                'status_key': status_key,
                'status_args': status_args,
                'type': 'folder'
            })
    except Exception as e:
        logger.error(f"Error analyzing folders: {e}")
        
    return items

def process_batch(items, dest_folder, cleanup_mode, callback_progress=None):
    """
    Processes the selected items (create CBZ + cleanup).
    Returns stats dict.
    """
    stats = {
        "processed": 0,
        "errors": 0,
        "orig_bytes": 0,
        "final_bytes": 0
    }
    
    if not items:
        return stats
        
    total = len(items)
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    trash_root = Path(items[0]['path']).parent / "TO_DELETE"
    
    for i, item in enumerate(items):
        if callback_progress:
            callback_progress(i, total, item['name'])
            
        if not item['valid']:
            stats["errors"] += 1
            logger.warning(f"Skipping invalid item {item['name']}: {item['reason']}")
            continue
            
        source_path = Path(item['path'])
        cbz_name = source_path.name + ".cbz"
        cbz_path = dest_path / cbz_name
        
        try:
            # Compress
            with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                 for entry in os.scandir(source_path):
                        if entry.is_file() and is_valid_image(entry.name):
                            zf.write(entry.path, arcname=entry.name)
            
            final_size = cbz_path.stat().st_size
            stats["processed"] += 1
            stats["orig_bytes"] += item['orig_size']
            stats["final_bytes"] += final_size
            
            logger.info(f"Created CBZ: {cbz_name} ({format_bytes(final_size)})")
            
            # Cleanup
            move_original_to_trash(source_path, trash_root, dry_run=False, action_mode=cleanup_mode)
            
        except Exception as e:
             logger.error(f"Error processing {item['name']}: {e}")
             stats["errors"] += 1
             # Cleanup specific CBZ if failed
             if cbz_path.exists():
                 try: os.remove(cbz_path)
                 except: pass

    return stats

def move_original_to_trash(source_folder, trash_root, dry_run=False, action_mode="folder"):
    """
    Handles cleanup of processed folders.
    action_mode: 'folder' (default), 'recycle', 'none'
    """
    if action_mode == "none":
        return True # Indicate success for 'none' action

    source_path = Path(source_folder)
    
    if action_mode == "recycle":
        ok, msg = utils.send_to_recycle_bin(source_path)
        if ok:
             logger.info(f"Recycled: {source_path}")
             return True
        else:
             logger.error(f"Failed to recycle {source_path}: {msg}")
             return False

    # Default: MODE "folder" (TO_DELETE)
    trash_path = Path(trash_root) / source_path.name
    
    try:
        Path(trash_root).mkdir(parents=True, exist_ok=True)
        # Handle conflicts
        if trash_path.exists():
            import time
            timestamp = int(time.time())
            trash_path = Path(trash_root) / f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
        shutil.move(str(source_path), str(trash_path))
        logger.info(f"Moved original to processed folder: {trash_path.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to move original {source_path.name}: {e}")
        return False

def format_bytes(size):
    # Added helper here just in case, though gui has it too.
    # Logic usually doesn't need to format for logs unless explicitly requested.
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"
