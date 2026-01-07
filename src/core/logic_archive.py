# logic_archive.py - Logic for Mode 3: Archives to Comic Info (ZIP->CBZ, RAR->CBR)
import os
import shutil
import zipfile
from pathlib import Path
from utils.helpers import logger
import utils.helpers as utils
from core import logic_compress

def is_zip_with_images(zip_path):
    """
    Checks if a zip file contains at least one valid image.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if logic_compress.is_valid_image(name):
                    return True
        return False
    except zipfile.BadZipFile:
        return False



def scan_archives(source_folder):
    """
    Scans for .zip and .rar files.
    Returns list of items: [{id, path, name, orig_size, valid, target_ext, reason}]
    """
    items = []
    source_path = Path(source_folder)
    
    if not source_path.is_dir():
        return items
        
    try:
        files = sorted([f for f in os.scandir(source_path) if f.is_file()], key=lambda e: e.name)
        for i, entry in enumerate(files):
            file_path = Path(entry.path)
            ext = file_path.suffix.lower()
            
            if ext not in ['.zip', '.rar']:
                continue
                
            orig_size = entry.stat().st_size
            valid = True
            reason = ""
            target_ext = ""
            
            if ext == '.zip':
                if is_zip_with_images(file_path):
                    target_ext = ".cbz"
                    status_key = "status_convert"
                    status_args = ("CBZ",)
                    reason = "Llest - Es convertirà a CBZ"
                else:
                    valid = False
                    status_key = "status_invalid"
                    status_args = ("ZIP empty or no images",)
                    reason = "ZIP empty or no images"
            elif ext == '.rar':
                 target_ext = ".cbr"
                 status_key = "status_convert"
                 status_args = ("CBR",)
                 reason = "Llest - Es convertirà a CBR"
            
            items.append({
                'id': f"m3_{i}",
                'path': entry.path,
                'name': entry.name,
                'orig_size': orig_size,
                'valid': valid,
                'reason': reason,
                'status_key': status_key,
                'status_args': status_args,
                'target_ext': target_ext,
                'type': 'archive'
            })
            
    except Exception as e:
        logger.error(f"Error scanning archives: {e}")
        
    return items

def process_batch(items, dest_folder, cleanup_mode, callback_progress=None):
    stats = {
        "processed": 0,
        "errors": 0,
        "orig_bytes": 0,
        "final_bytes": 0
    }
    
    total = len(items)
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    trash_root = Path(items[0]['path']).parent / "TO_DELETE" if items else None

    for i, item in enumerate(items):
        if callback_progress:
            callback_progress(i, total, item['name'])
            
        if not item['valid']:
             continue
             
        source_path = Path(item['path'])
        
        # If dest is same as source parent, rename logic requires care
        # But we default dest to "CBZ_Output" usually.
        # If dest is different: copy/convert
        
        new_name = source_path.stem + item['target_ext']
        dest_file = dest_path / new_name
        
        try:
            shutil.copy2(source_path, dest_file)
            stats["processed"] += 1
            stats["orig_bytes"] += item['orig_size']
            
            try:
                stats["final_bytes"] += dest_file.stat().st_size
            except:
                 stats["final_bytes"] += item['orig_size']
                 
            logger.info(f"Converted: {dest_file.name}")
            
            logic_compress.move_original_to_trash(source_path, trash_root, dry_run=False, action_mode=cleanup_mode)
            
        except Exception as e:
            logger.error(f"Failed to process {item['name']}: {e}")
            stats["errors"] += 1
            
    return stats

def move_to_trash(file_path, trash_root, dry_run=False, action_mode="folder"):
    """
    Moves a single file to trash or recycle bin.
    """
    if action_mode == "none":
        return

    if action_mode == "recycle":
        if dry_run:
            logger.info(f"[DRY-RUN] S'hauria enviat a la paperera: {file_path}")
            return
        ok, msg = utils.send_to_recycle_bin(file_path)
        if ok:
             logger.info(f"Recycled: {file_path.name}")
        else:
             logger.error(f"Failed to recycle {file_path.name}: {msg}")
        return

    # Folder mode
    trash_path = Path(trash_root) / file_path.name
    
    if dry_run:
        logger.info(f"[DRY-RUN] S'hauria mogut l'original {file_path.name} a {trash_path}")
        return
        
    try:
        Path(trash_root).mkdir(parents=True, exist_ok=True)
        # Handle conflicts
        if trash_path.exists():
            import time
            timestamp = int(time.time())
            trash_path = Path(trash_root) / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
        shutil.move(str(file_path), str(trash_path))
        logger.info(f"Moved original to processed folder: {trash_path.name}")
    except Exception as e:
        logger.error(f"Failed to move original {file_path.name}: {e}")
