"""
Cloud Storage Integration Module
Handles uploading and managing podcast files in Google Cloud Storage
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import hashlib

try:
    from google.cloud import storage
    CLOUD_STORAGE_AVAILABLE = True
except ImportError:
    CLOUD_STORAGE_AVAILABLE = False

logger = logging.getLogger(__name__)

class CloudStorageManager:
    """Manages podcast file storage in Google Cloud Storage"""
    
    def __init__(self, config):
        self.config = config
        self.client = None
        self.bucket = None
        self.storage_available = False
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize Google Cloud Storage client"""
        if not CLOUD_STORAGE_AVAILABLE:
            logger.warning("Google Cloud Storage library not available")
            return
        
        try:
            # Initialize client - will use service account or default credentials
            self.client = storage.Client(project=self.config.PROJECT_ID)
            
            # Get or create bucket
            bucket_name = self.config.CLOUD_STORAGE_BUCKET
            self.bucket = self.client.bucket(bucket_name)
            
            # Test bucket access
            if self.bucket.exists():
                logger.info(f"Connected to existing Cloud Storage bucket: {bucket_name}")
            else:
                logger.warning(f"Bucket {bucket_name} does not exist - will attempt to create")
                self._create_bucket_if_needed()
            
            self.storage_available = True
            logger.info("Cloud Storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Storage: {str(e)}")
            self.storage_available = False
    
    def _create_bucket_if_needed(self):
        """Create bucket if it doesn't exist"""
        try:
            bucket_name = self.config.CLOUD_STORAGE_BUCKET
            
            # Create bucket with appropriate settings for podcast files
            bucket = self.client.create_bucket(
                bucket_name,
                location="US-CENTRAL1",  # Choose appropriate region
                timeout=30
            )
            
            # Set bucket to be publicly readable for podcast access
            bucket.make_public(recursive=True, future=True)
            
            logger.info(f"Created Cloud Storage bucket: {bucket_name}")
            self.bucket = bucket
            
        except Exception as e:
            logger.error(f"Failed to create bucket: {str(e)}")
            raise
    
    def upload_podcast(self, local_file_path: str, 
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Upload podcast file to Cloud Storage
        
        Args:
            local_file_path (str): Path to local podcast file
            metadata (dict): Optional metadata for the file
            
        Returns:
            dict: Upload result with public URL and metadata
        """
        if not self.storage_available:
            logger.warning("Cloud Storage not available - podcast saved locally only")
            return {
                'success': False,
                'error': 'Cloud Storage not available',
                'local_file': local_file_path,
                'fallback_used': True
            }
        
        if not os.path.exists(local_file_path):
            return {
                'success': False,
                'error': f'Local file not found: {local_file_path}',
                'fallback_used': False
            }
        
        try:
            # Generate cloud storage filename
            cloud_filename = self._generate_cloud_filename(local_file_path, metadata)
            
            logger.info(f"Uploading podcast to Cloud Storage: {cloud_filename}")
            
            # Create blob and upload
            blob = self.bucket.blob(cloud_filename)
            
            # Set metadata
            blob.metadata = {
                'created_at': datetime.utcnow().isoformat(),
                'original_filename': os.path.basename(local_file_path),
                'file_type': 'podcast',
                'service': 'news-extraction',
                **(metadata or {})
            }
            
            # Set content type for audio files
            blob.content_type = 'audio/mpeg'
            
            # Upload file
            with open(local_file_path, 'rb') as file_data:
                blob.upload_from_file(file_data, timeout=300)
            
            # Make blob publicly accessible
            blob.make_public()
            
            # Get file info
            file_size = os.path.getsize(local_file_path) / (1024 * 1024)  # MB
            public_url = blob.public_url
            # More thorough URL cleaning
            import re
            public_url = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', '', str(public_url)).strip()
            logger.info(f"Podcast uploaded successfully: {public_url}")
            
            # Clean up local file after successful upload (optional)
            if self.config.PODCAST_RETENTION_DAYS > 0:
                self._schedule_cleanup()
            
            return {
                'success': True,
                'public_url': public_url,
                'cloud_filename': cloud_filename,
                'file_size_mb': file_size,
                'bucket_name': self.config.CLOUD_STORAGE_BUCKET,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'fallback_used': False
            }
            
        except Exception as e:
            logger.error(f"Failed to upload podcast to Cloud Storage: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'local_file': local_file_path,
                'fallback_used': True
            }
    
    def _generate_cloud_filename(self, local_file_path: str, 
                                metadata: Dict[str, Any] = None) -> str:
        """Generate a unique filename for cloud storage"""
        # Extract base filename
        base_name = os.path.splitext(os.path.basename(local_file_path))[0]
        extension = os.path.splitext(local_file_path)[1]
        
        # Add timestamp for uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Add hash for additional uniqueness
        file_hash = hashlib.md5(f"{base_name}_{timestamp}".encode()).hexdigest()[:8]
        
        # Construct cloud filename
        cloud_filename = f"podcasts/{timestamp}_{base_name}_{file_hash}{extension}"
        
        return cloud_filename
    
    def list_podcasts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent podcasts in Cloud Storage
        
        Args:
            limit (int): Maximum number of podcasts to return
            
        Returns:
            list: List of podcast information
        """
        if not self.storage_available:
            return []
        
        try:
            podcasts = []
            
            # List blobs with podcast prefix
            blobs = self.bucket.list_blobs(prefix="podcasts/", max_results=limit)
            
            for blob in blobs:
                # Clean URL thoroughly
                import re
                clean_url = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', '', str(blob.public_url)).strip()
                
                podcast_info = {
                    'filename': blob.name,
                    'public_url': clean_url,
                    'size_bytes': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'content_type': blob.content_type,
                    'metadata': blob.metadata or {}
                }
                podcasts.append(podcast_info)
            
            # Sort by creation time (newest first)
            podcasts.sort(key=lambda x: x['created'] or '', reverse=True)
            
            logger.info(f"Found {len(podcasts)} podcasts in Cloud Storage")
            return podcasts
            
        except Exception as e:
            logger.error(f"Failed to list podcasts: {str(e)}")
            return []
    
    def cleanup_old_podcasts(self, retention_days: int = None) -> Dict[str, Any]:
        """
        Clean up podcasts older than retention period
        
        Args:
            retention_days (int): Days to keep podcasts (uses config default if None)
            
        Returns:
            dict: Cleanup results
        """
        if not self.storage_available:
            return {'success': False, 'error': 'Cloud Storage not available'}
        
        if retention_days is None:
            retention_days = self.config.PODCAST_RETENTION_DAYS
        
        if retention_days <= 0:
            logger.info("Podcast cleanup disabled (retention_days <= 0)")
            return {'success': True, 'message': 'Cleanup disabled', 'deleted_count': 0}
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            deleted_count = 0
            deleted_files = []
            errors = []
            
            # List all podcast blobs
            blobs = self.bucket.list_blobs(prefix="podcasts/")
            
            for blob in blobs:
                # Check if blob is older than cutoff
                if blob.time_created and blob.time_created.replace(tzinfo=None) < cutoff_date:
                    try:
                        logger.info(f"Deleting old podcast: {blob.name}")
                        blob.delete()
                        deleted_count += 1
                        deleted_files.append({
                            'filename': blob.name,
                            'created': blob.time_created.isoformat() if blob.time_created else None
                        })
                    except Exception as e:
                        error_msg = f"Failed to delete {blob.name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            result = {
                'success': True,
                'deleted_count': deleted_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'deleted_files': deleted_files,
                'cleanup_timestamp': datetime.utcnow().isoformat()
            }
            
            if errors:
                result['errors'] = errors
            
            logger.info(f"Podcast cleanup completed: {deleted_count} files deleted")
            return result
            
        except Exception as e:
            logger.error(f"Podcast cleanup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'deleted_count': 0
            }
    
    def _schedule_cleanup(self):
        """Schedule periodic cleanup (called after successful uploads)"""
        # This could trigger cleanup, but for now we'll do it manually
        # In production, this could be handled by a separate Cloud Function
        pass
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        if not self.storage_available:
            return {'available': False}
        
        try:
            podcasts = self.list_podcasts(limit=1000)  # Get more for stats
            
            total_size = sum(p.get('size_bytes', 0) for p in podcasts)
            total_size_mb = total_size / (1024 * 1024)
            
            stats = {
                'available': True,
                'total_podcasts': len(podcasts),
                'total_size_mb': round(total_size_mb, 2),
                'bucket_name': self.config.CLOUD_STORAGE_BUCKET,
                'retention_days': self.config.PODCAST_RETENTION_DAYS,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            if podcasts:
                stats['latest_podcast'] = podcasts[0]['created']
                stats['oldest_podcast'] = podcasts[-1]['created']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                'available': True,
                'error': str(e)
            }

def upload_podcast_to_cloud(local_file_path: str, config, 
                           metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenient function to upload podcast to Cloud Storage
    
    Args:
        local_file_path (str): Path to local podcast file
        config: Configuration object
        metadata (dict): Optional file metadata
        
    Returns:
        dict: Upload result
    """
    storage_manager = CloudStorageManager(config)
    return storage_manager.upload_podcast(local_file_path, metadata)