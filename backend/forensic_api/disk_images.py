"""
Disk image management utilities
"""
import os
from pathlib import Path
from datetime import datetime


def get_available_disk_images():
    """
    Get list of available disk images from data/samples directory
    
    Returns:
        list: List of disk image info dictionaries
    """
    # Get the data/samples directory
    base_dir = Path(__file__).parent.parent.parent
    samples_dir = base_dir / 'data' / 'samples'
    
    if not samples_dir.exists():
        samples_dir.mkdir(parents=True, exist_ok=True)
        return []
    
    # Supported disk image extensions
    image_extensions = ['.E01', '.E02', '.dd', '.raw', '.img', '.001', '.aff', '.afd']
    
    images = []
    
    # Scan directory for disk images
    for file_path in samples_dir.iterdir():
        if file_path.is_file():
            # Check if file has supported extension (case-insensitive)
            if any(file_path.suffix.upper() == ext.upper() for ext in image_extensions):
                # Get file stats
                stat = file_path.stat()
                
                # Format size
                size_bytes = stat.st_size
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
                
                images.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size': size_bytes,
                    'size_formatted': size_str,
                    'extension': file_path.suffix,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
    
    # Sort by filename
    images.sort(key=lambda x: x['filename'])
    
    return images


def get_disk_image_path(filename):
    """
    Get full path to a disk image by filename
    
    Args:
        filename: Name of the disk image file
    
    Returns:
        str: Full path to the disk image, or None if not found
    """
    base_dir = Path(__file__).parent.parent.parent
    samples_dir = base_dir / 'data' / 'samples'
    
    image_path = samples_dir / filename
    
    if image_path.exists() and image_path.is_file():
        return str(image_path)
    
    return None
