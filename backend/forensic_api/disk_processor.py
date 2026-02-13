"""
Disk image processor for forensic analysis
Handles disk image upload, extraction, and artifact storage
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from extraction.disk_extractor import ForensicDiskExtractor
from database.mongodb_storage import ForensicMongoStorage

logger = logging.getLogger(__name__)


class DiskImageProcessor:
    """Process disk images and extract forensic artifacts"""
    
    def __init__(self, data_dir=None):
        """
        Initialize disk image processor
        
        Args:
            data_dir: Directory containing disk images (default: forensic_ir_app/data)
        """
        if data_dir is None:
            # Default to forensic_ir_app/data directory
            base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / 'data'
        
        self.data_dir = Path(data_dir)
        self.samples_dir = self.data_dir / 'samples'
        self.extracted_dir = self.data_dir / 'extracted'
        self.processed_dir = self.data_dir / 'processed'
        
        # Create directories if they don't exist
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.extractor = ForensicDiskExtractor()
        self.storage = ForensicMongoStorage()
    
    def list_available_images(self):
        """List all available disk images in the samples directory"""
        if not self.samples_dir.exists():
            return []
        
        image_extensions = ['.E01', '.dd', '.raw', '.img', '.001']
        images = []
        
        for file in self.samples_dir.iterdir():
            if file.is_file() and any(file.suffix.upper() == ext.upper() for ext in image_extensions):
                images.append({
                    'filename': file.name,
                    'path': str(file),
                    'size': file.stat().st_size,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                })
        
        return images
    
    def process_disk_image(self, case_id, disk_image_path, output_format='json'):
        """
        Process a disk image and extract artifacts
        
        Args:
            case_id: Unique case identifier
            disk_image_path: Path to disk image file
            output_format: Output format ('json' or 'mongodb')
        
        Returns:
            dict: Processing results with artifact counts
        """
        try:
            logger.info(f"Processing disk image for case {case_id}: {disk_image_path}")
            
            # Create output directory for this case
            case_output_dir = self.extracted_dir / case_id
            case_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract artifacts
            logger.info("Extracting artifacts from disk image...")
            artifacts = self.extractor.extract_all_artifacts(
                disk_image_path,
                str(case_output_dir)
            )
            
            # Count artifacts by type
            artifact_counts = {}
            for artifact_type, artifact_list in artifacts.items():
                artifact_counts[artifact_type] = len(artifact_list) if artifact_list else 0
            
            # Save to JSON
            json_output_path = self.processed_dir / f"{case_id}_artifacts.json"
            logger.info(f"Saving artifacts to {json_output_path}")
            
            # Prepare artifacts for JSON serialization
            serializable_artifacts = {}
            for artifact_type, artifact_list in artifacts.items():
                if artifact_list:
                    serializable_artifacts[artifact_type] = artifact_list
            
            with open(json_output_path, 'w') as f:
                json.dump({
                    'case_id': case_id,
                    'disk_image': os.path.basename(disk_image_path),
                    'processed_at': datetime.now().isoformat(),
                    'artifact_counts': artifact_counts,
                    'artifacts': serializable_artifacts
                }, f, indent=2, default=str)
            
            # Store in MongoDB if requested
            if output_format == 'mongodb' or output_format == 'both':
                logger.info("Storing artifacts in MongoDB...")
                self.storage.store_all_artifacts(str(json_output_path))
            
            logger.info(f"Processing complete. Total artifacts: {sum(artifact_counts.values())}")
            
            return {
                'success': True,
                'case_id': case_id,
                'disk_image': os.path.basename(disk_image_path),
                'json_output': str(json_output_path),
                'artifact_counts': artifact_counts,
                'total_artifacts': sum(artifact_counts.values()),
                'processed_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error processing disk image: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'case_id': case_id,
            }
    
    def get_case_artifacts(self, case_id):
        """
        Get processed artifacts for a case
        
        Args:
            case_id: Case identifier
        
        Returns:
            dict: Artifact data or None if not found
        """
        json_path = self.processed_dir / f"{case_id}_artifacts.json"
        
        if not json_path.exists():
            return None
        
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading artifacts for case {case_id}: {e}")
            return None
    
    def delete_case_artifacts(self, case_id):
        """
        Delete processed artifacts for a case
        
        Args:
            case_id: Case identifier
        
        Returns:
            bool: True if successful
        """
        try:
            # Delete JSON file
            json_path = self.processed_dir / f"{case_id}_artifacts.json"
            if json_path.exists():
                json_path.unlink()
            
            # Delete extracted directory
            case_output_dir = self.extracted_dir / case_id
            if case_output_dir.exists():
                import shutil
                shutil.rmtree(case_output_dir)
            
            logger.info(f"Deleted artifacts for case {case_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting artifacts for case {case_id}: {e}")
            return False
    
    def close(self):
        """Close connections"""
        self.storage.close()


# Singleton instance
_processor_instance = None

def get_disk_processor():
    """Get or create disk processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = DiskImageProcessor()
    return _processor_instance
