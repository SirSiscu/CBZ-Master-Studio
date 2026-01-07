import os
import re
import shutil
from pathlib import Path
from utils.helpers import logger
from core import logic_compress

def analyze_loose_images(folder_path, merge_chapters=False):
    """
    Detects patterns and proposes grouping.
    Returns list of items: [{id, name, orig_size, valid, reason, type, files, dest_name}]
    """
    path = Path(folder_path)
    if not path.is_dir():
        return []

    groups = {}
    
    # Analysis logic (same regex strategy)
    for entry in os.scandir(path):
        if entry.is_file() and logic_compress.is_valid_image(entry.name):
            name = entry.name
            
            # Regex detection
            chapter_match = re.search(r"(.+?)(?:[\s_\-]+)(ch|chapter|chap|cap|c)(?:[\s_\-\.]*)(\d+)", name, re.IGNORECASE)
            series_name = ""
            
            if chapter_match:
                base_series = chapter_match.group(1).strip()
                chap_type = chapter_match.group(2)
                chap_num = chapter_match.group(3)
                
                if merge_chapters:
                    series_name = base_series
                else:
                    series_name = f"{base_series} {chap_type}{chap_num}"
            else:
                fallback_match = re.match(r"^(.*?)(?:[\s_\-]*)(\d+)(?:.*)\.", name)
                if fallback_match:
                    series_name = fallback_match.group(1).strip()
                
            if not series_name:
                continue

            series_name = series_name.strip(" -_")

            if series_name not in groups:
                 groups[series_name] = []
            groups[series_name].append(entry)
            
    # Convert groups dict to items list
    items = []
    for i, (s_name, entries) in enumerate(groups.items()):
        total_size = sum(e.stat().st_size for e in entries)
        file_paths = [e.path for e in entries]
        
        items.append({
            'id': f"m2_{i}",
            'name': s_name, # This will be the folder name
            'orig_size': total_size,
            'valid': True,
            'reason': f"Llest - {len(entries)} imatges",
            'status_key': "status_img_count",
            'status_args': (len(entries),),
            'type': 'group',
            'files': file_paths,
            'dest_name': s_name
        })
        
    return items

def process_batch(items, dest_folder, callback_progress=None):
    """
    Executes the grouping.
    items: Selected groups to create.
    """
    stats = {
        "processed": 0, # Files moved
        "errors": 0,
        "orig_bytes": 0,
        "final_bytes": 0,
        "created_folders": 0
    }
    
    dest_path = Path(dest_folder)
    total = len(items)
    
    for i, item in enumerate(items):
        if callback_progress:
            callback_progress(i, total, item['name'])
            
        if not item['valid']:
            continue
            
        target_dir = dest_path / item['dest_name']
        
        try:
            target_dir.mkdir(exist_ok=True, parents=True)
            stats["created_folders"] += 1
            
            for file_p in item['files']:
                try:
                    src = Path(file_p)
                    # Handle name collision if file exists
                    dst = target_dir / src.name
                    if dst.exists():
                         # Timestamp collision fix
                         import time
                         dst = target_dir / f"{src.stem}_{int(time.time())}{src.suffix}"
                         
                    shutil.move(str(src), str(dst))
                    stats["processed"] += 1
                    # In Mode 2, bytes don't change, just location
                except Exception as e:
                    logger.error(f"Failed to move {file_p}: {e}")
                    stats["errors"] += 1
            
            # Update bytes stats after success (approximate)
            stats["orig_bytes"] += item['orig_size']
            stats["final_bytes"] += item['orig_size']
            
            logger.info(f"Grouped: {item['name']} ({len(item['files'])} files)")
            
        except Exception as e:
             logger.error(f"Failed to create group folder {target_dir}: {e}")
             stats["errors"] += 1
             
    return stats
