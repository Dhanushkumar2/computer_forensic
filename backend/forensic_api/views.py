"""
Django REST Framework views for forensic API
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from datetime import datetime, timedelta
import json
import logging

from .models import (
    ForensicCase, CaseNote, CaseFile, ExtractionJob,
    SearchQuery, UserProfile, AuditLog
)
from .serializers import (
    ForensicCaseSerializer, CaseNoteSerializer, CaseFileSerializer,
    ExtractionJobSerializer, SearchQuerySerializer, UserProfileSerializer,
    AuditLogSerializer, BrowserArtifactSerializer, USBDeviceSerializer,
    UserActivitySerializer, TimelineEventSerializer, CaseSummarySerializer,
    SearchResultsSerializer, StatisticsSerializer, RegistryArtifactSerializer,
    EventLogArtifactSerializer, FileSystemArtifactSerializer, DeletedFileSerializer,
    InstalledProgramSerializer, AndroidArtifactSerializer, MLAnomalySerializer,
    AndroidMLAnomalySerializer
)
from .mongodb_service import mongo_service
from .disk_processor import get_disk_processor
from .disk_images import get_available_disk_images, get_disk_image_path
from .utils import log_audit_action, get_client_ip
from extraction.basic_info import compute_basic_info
import pyewf
from pathlib import Path
import os
import threading
from ai_ml.model_infer import run_gat_inference
from ai_ml.android_model_infer import run_android_inference

logger = logging.getLogger(__name__)


def _get_image_size(image_path):
    ext = Path(image_path).suffix.lower()
    if ext in {'.e01', '.e02', '.e03', '.e04', '.e05'}:
        ewf_files = pyewf.glob(image_path)
        handle = pyewf.handle()
        handle.open(ewf_files)
        size = handle.get_media_size()
        handle.close()
        return size
    return os.path.getsize(image_path)


def _read_image_chunk(image_path, start_offset, length):
    ext = Path(image_path).suffix.lower()
    if ext in {'.e01', '.e02', '.e03', '.e04', '.e05'}:
        ewf_files = pyewf.glob(image_path)
        handle = pyewf.handle()
        handle.open(ewf_files)
        handle.seek(start_offset)
        data = handle.read(length)
        handle.close()
        return data
    with open(image_path, 'rb') as f:
        f.seek(start_offset)
        return f.read(length)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class ForensicCaseViewSet(viewsets.ModelViewSet):
    """ViewSet for forensic cases"""
    
    serializer_class = ForensicCaseSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]  # Allow any for development
    
    def get_queryset(self):
        """Get cases based on user permissions"""
        user = self.request.user
        queryset = ForensicCase.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Search by title or case_id
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(case_id__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='mongo-cases')
    def mongo_cases(self, request):
        """Return cases from MongoDB, mapped to Django IDs when possible."""
        try:
            mongo_cases = mongo_service.retrieval.get_all_cases()
        except Exception as e:
            logger.error(f"Error loading MongoDB cases: {e}", exc_info=True)
            return Response({'error': 'Failed to load cases from MongoDB'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        results = []
        for doc in mongo_cases:
            case_id = doc.get('case_id')
            django_case = None
            if case_id:
                django_case = ForensicCase.objects.filter(case_id=case_id).first()

            cleaned = {
                'id': django_case.id if django_case else None,
                'case_id': case_id,
                'image_path': doc.get('image_path'),
                'extraction_time': doc.get('extraction_time'),
                'status': doc.get('status'),
                'summary': doc.get('summary', {}),
            }
            results.append(cleaned)

        return Response(results)

    @action(detail=False, methods=['post'], url_path='import-mongo')
    def import_mongo_case(self, request):
        """Create a Django case from a MongoDB case_id."""
        case_id = request.data.get('case_id')
        if not case_id:
            return Response({'error': 'case_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Already exists?
        existing = ForensicCase.objects.filter(case_id=case_id).first()
        if existing:
            serializer = ForensicCaseSerializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)

        try:
            case_doc = mongo_service.get_case_info(case_id)
        except Exception as e:
            logger.error(f"Error loading MongoDB case {case_id}: {e}", exc_info=True)
            return Response({'error': 'Failed to load MongoDB case'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not case_doc:
            return Response({'error': 'MongoDB case not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get or create a default user for development
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@forensic.local', 'is_staff': True}
        )

        case_details = case_doc.get('case_details', {}) or {}
        image_path = case_doc.get('image_path') or case_details.get('image_path', '')
        image_name = os.path.basename(image_path) if image_path else ''

        case = ForensicCase.objects.create(
            case_id=case_id,
            title=case_details.get('title') or case_id,
            description=case_details.get('description', ''),
            case_number=case_details.get('case_number', ''),
            image_path=image_path,
            image_name=image_name,
            image_size=case_details.get('image_size'),
            status=case_doc.get('status', 'completed'),
            priority=case_details.get('priority', 'medium'),
            extraction_time=case_doc.get('extraction_time'),
            ntfs_offset=case_doc.get('ntfs_offset'),
            user_profiles=case_doc.get('user_profiles', []),
            created_by=user,
            assigned_to=user,
        )

        serializer = ForensicCaseSerializer(case)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Create a new case, persist metadata to MongoDB, and trigger processing"""
        # Get or create a default user for development
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@forensic.local', 'is_staff': True}
        )
        
        # Save case with user
        case = serializer.save(created_by=user, assigned_to=user)
        
        # Log action (skip if user is not authenticated)
        if self.request.user.is_authenticated:
            log_audit_action(
                self.request.user, 'create', 'case', case.case_id,
                {'title': case.title}, self.request
            )
        
        # Check if disk image filename is provided (selecting from existing)
        disk_image_filename = self.request.data.get('disk_image_filename')
        
        # Case summary can come as JSON payload or JSON string (multipart)
        case_summary = self.request.data.get('case_summary')
        if isinstance(case_summary, str) and case_summary.strip():
            try:
                case_summary = json.loads(case_summary)
            except json.JSONDecodeError:
                logger.warning("Invalid case_summary JSON string for case %s", case.case_id)
                case_summary = None

        # Check if raw/disk image file is uploaded
        disk_image = self.request.FILES.get('raw_file') or self.request.FILES.get('disk_image')
        raw_file_info = None
        
        if disk_image_filename:
            # User selected an existing disk image
            file_path = get_disk_image_path(disk_image_filename)
            if not file_path:
                logger.error(f"Disk image not found: {disk_image_filename}")
                return
            
            # Update case with image information
            case.image_path = file_path
            case.image_name = disk_image_filename
            case.save()
            raw_file_info = {
                'filename': disk_image_filename,
                'path': file_path,
                'uploaded': False,
            }
            
            # Create extraction job
            job = ExtractionJob.objects.create(
                case=case,
                source_path=file_path,
                status='queued'
            )
            
            # Start processing
            self._start_processing(case, job, file_path)
            
        elif disk_image:
            # Save the disk image file
            from django.conf import settings
            import os
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(settings.BASE_DIR, '..', 'data', 'samples')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, disk_image.name)
            with open(file_path, 'wb+') as destination:
                for chunk in disk_image.chunks():
                    destination.write(chunk)
            
            # Update case with image information
            case.image_path = file_path
            case.image_name = disk_image.name
            case.image_size = disk_image.size
            case.save()
            raw_file_info = {
                'filename': disk_image.name,
                'path': file_path,
                'size': disk_image.size,
                'uploaded': True,
            }
            
            # Create extraction job
            job = ExtractionJob.objects.create(
                case=case,
                source_path=file_path,
                status='queued'
            )
            
            # Start processing
            self._start_processing(case, job, file_path)

        # Persist case details + summary in MongoDB at case creation time
        case_details = {
            'title': case.title,
            'description': case.description,
            'case_number': case.case_number,
            'priority': case.priority,
            'status': case.status,
            'image_name': case.image_name,
            'image_path': case.image_path,
            'image_size': case.image_size,
            'created_by': getattr(case.created_by, 'username', None),
            'created_at': case.created_at.isoformat() if case.created_at else None,
            'updated_at': case.updated_at.isoformat() if case.updated_at else None,
        }
        try:
            mongo_service.upsert_case_record(
                case_id=case.case_id,
                case_details=case_details,
                summary=case_summary if isinstance(case_summary, dict) else None,
                raw_file_info=raw_file_info,
                status=case.status
            )
        except Exception as e:
            logger.error("Failed to upsert case %s in MongoDB: %s", case.case_id, e, exc_info=True)
    
    def _start_processing(self, case, job, file_path):
        """Start disk image processing in background thread"""
        def process_disk_image():
            try:
                job.status = 'running'
                job.started_at = datetime.now()
                job.save()
                
                logger.info(f"Starting disk image processing for case {case.case_id}")
                
                processor = get_disk_processor()
                result = processor.process_disk_image(
                    case.case_id,
                    file_path,
                    output_format='mongodb'
                )
                
                if result['success']:
                    job.status = 'completed'
                    job.artifacts_extracted = result.get('total_artifacts', 0)
                    job.completed_at = datetime.now()
                    job.progress_percentage = 100
                    case.status = 'active'
                    case.save()
                    logger.info(f"Successfully processed {job.artifacts_extracted} artifacts for case {case.case_id}")
                else:
                    job.status = 'failed'
                    job.error_message = result.get('error', 'Unknown error')
                    case.status = 'failed'
                    case.save()
                    logger.error(f"Failed to process disk image for case {case.case_id}: {job.error_message}")
                
                job.save()
                
            except Exception as e:
                logger.error(f"Error processing disk image for case {case.case_id}: {e}", exc_info=True)
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.now()
                job.save()
                case.status = 'failed'
                case.save()
        
        # Start background thread
        thread = threading.Thread(target=process_disk_image)
        thread.daemon = True
        thread.start()
        logger.info(f"Started disk image processing thread for case {case.case_id}")
    
    def perform_update(self, serializer):
        """Update a case"""
        case = serializer.save()
        if self.request.user.is_authenticated:
            log_audit_action(
                self.request.user, 'update', 'case', case.case_id,
                serializer.validated_data, self.request
            )
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get case summary from MongoDB"""
        case = self.get_object()
        
        try:
            summary = mongo_service.get_case_summary(case.case_id)
            if summary:
                serializer = CaseSummarySerializer(summary)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Case summary not found in MongoDB'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error getting case summary: {e}")
            return Response(
                {'error': 'Failed to retrieve case summary'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='basic-info')
    def basic_info(self, request, pk=None):
        """Get basic disk information for the case image."""
        case = self.get_object()
        if not case.image_path or not os.path.exists(case.image_path):
            return Response(
                {'error': 'Disk image not found for this case'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check cached basic_info in MongoDB
        cached = None
        try:
            case_doc = mongo_service.get_case_info(case.case_id)
            cached = case_doc.get('basic_info') if case_doc else None
        except Exception:
            cached = None

        if cached:
            return Response({'case_id': case.case_id, 'basic_info': cached})

        # Compute and cache
        try:
            basic_info = compute_basic_info(case.image_path)
            mongo_service.upsert_case_record(
                case_id=case.case_id,
                case_details={'image_path': case.image_path},
                summary=None,
                raw_file_info=None,
                status=case.status
            )
            # Update basic info in the case record
            mongo_service.storage.collections['cases'].update_one(
                {'case_id': case.case_id},
                {'$set': {'basic_info': basic_info}}
            )
            return Response({'case_id': case.case_id, 'basic_info': basic_info})
        except Exception as e:
            logger.error(f"Error computing basic_info: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to compute basic info'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='raw-extraction-status')
    def raw_extraction_status(self, request, pk=None):
        """Return raw extraction progress for the case."""
        case = self.get_object()
        if not case.image_path or not os.path.exists(case.image_path):
            return Response(
                {'error': 'Disk image not found for this case'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            total_size = _get_image_size(case.image_path)
        except Exception as e:
            logger.error(f"Error getting image size: {e}", exc_info=True)
            return Response({'error': 'Failed to get image size'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        case_doc = mongo_service.get_case_info(case.case_id) or {}
        ranges = case_doc.get('raw_extractions', [])
        extracted_bytes = sum(r.get('size', 0) for r in ranges if isinstance(r.get('size', 0), int))
        next_start = max((r.get('end_offset', 0) for r in ranges), default=0)
        percent = (extracted_bytes / total_size) * 100 if total_size else 0

        return Response({
            'case_id': case.case_id,
            'total_size': total_size,
            'extracted_bytes': extracted_bytes,
            'percent': round(percent, 2),
            'ranges': ranges,
            'next_start_offset': next_start
        })

    @action(detail=True, methods=['post'], url_path='extract-raw')
    def extract_raw(self, request, pk=None):
        """Extract a raw chunk of data from the disk image."""
        case = self.get_object()
        if not case.image_path or not os.path.exists(case.image_path):
            return Response(
                {'error': 'Disk image not found for this case'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            total_size = _get_image_size(case.image_path)
        except Exception as e:
            logger.error(f"Error getting image size: {e}", exc_info=True)
            return Response({'error': 'Failed to get image size'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        case_doc = mongo_service.get_case_info(case.case_id) or {}
        ranges = case_doc.get('raw_extractions', [])
        next_start = max((r.get('end_offset', 0) for r in ranges), default=0)

        # Inputs: start_offset (bytes) optional, size_mb or length_bytes required
        start_offset = request.data.get('start_offset')
        length_bytes = request.data.get('length_bytes')
        size_mb = request.data.get('size_mb')

        try:
            if start_offset is None or start_offset == '':
                start_offset = next_start
            start_offset = int(start_offset)
            if length_bytes is None and size_mb is None:
                return Response({'error': 'Provide length_bytes or size_mb'}, status=status.HTTP_400_BAD_REQUEST)
            if length_bytes is None:
                length_bytes = int(float(size_mb) * 1024 * 1024)
            else:
                length_bytes = int(length_bytes)
        except Exception:
            return Response({'error': 'Invalid numeric input'}, status=status.HTTP_400_BAD_REQUEST)

        if start_offset < 0 or length_bytes <= 0:
            return Response({'error': 'Invalid range'}, status=status.HTTP_400_BAD_REQUEST)

        end_offset = min(start_offset + length_bytes, total_size)
        length_bytes = end_offset - start_offset
        if length_bytes <= 0:
            return Response({'error': 'Range exceeds disk size'}, status=status.HTTP_400_BAD_REQUEST)

        # Avoid overlapping ranges
        for r in ranges:
            r_start = r.get('start_offset', 0)
            r_end = r.get('end_offset', 0)
            if max(r_start, start_offset) < min(r_end, end_offset):
                return Response({'error': 'Requested range overlaps existing extraction'}, status=status.HTTP_409_CONFLICT)

        # Write output chunk
        output_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'partial'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{case.case_id}_{start_offset}_{end_offset}.bin"

        try:
            data = _read_image_chunk(case.image_path, start_offset, length_bytes)
            with open(output_file, 'wb') as f:
                f.write(data)
        except Exception as e:
            logger.error(f"Error extracting raw chunk: {e}", exc_info=True)
            return Response({'error': 'Failed to extract raw chunk'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        extraction_doc = {
            'start_offset': start_offset,
            'end_offset': end_offset,
            'size': length_bytes,
            'output_file': str(output_file),
            'created_at': datetime.now().isoformat()
        }

        # Persist to Mongo case document
        try:
            mongo_service.storage.collections['cases'].update_one(
                {'case_id': case.case_id},
                {'$push': {'raw_extractions': extraction_doc}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving raw extraction metadata: {e}", exc_info=True)

        return Response({
            'case_id': case.case_id,
            'range': extraction_doc,
            'total_size': total_size
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get case statistics"""
        case = self.get_object()
        
        try:
            stats = mongo_service.get_case_statistics(case.case_id)
            serializer = StatisticsSerializer({'case_id': case.case_id, **stats})
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting case statistics: {e}")
            return Response(
                {'error': 'Failed to retrieve case statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def processing_status(self, request, pk=None):
        """Get disk image processing status"""
        case = self.get_object()
        
        try:
            # Get latest extraction job for this case
            job = ExtractionJob.objects.filter(case=case).order_by('-created_at').first()
            
            if not job:
                return Response({
                    'status': 'no_job',
                    'message': 'No extraction job found for this case'
                })
            
            return Response({
                'status': job.status,
                'artifacts_extracted': job.artifacts_extracted or 0,
                'created_at': job.created_at,
                'completed_at': job.completed_at,
                'error_message': job.error_message,
                'source_path': job.source_path,
            })
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return Response(
                {'error': 'Failed to retrieve processing status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='browser-history')
    def browser_history(self, request, pk=None):
        """Get browser history for case"""
        case = self.get_object()
        browser_type = request.query_params.get('browser_type')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        try:
            history = mongo_service.get_browser_history(case.case_id, browser_type, limit, offset)
            serializer = BrowserArtifactSerializer(history, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting browser history: {e}")
            return Response(
                {'error': 'Failed to retrieve browser history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='browser-cookies')
    def browser_cookies(self, request, pk=None):
        """Get browser cookies for case"""
        case = self.get_object()
        browser_type = request.query_params.get('browser_type')
        host = request.query_params.get('host')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        try:
            cookies = mongo_service.get_browser_cookies(case.case_id, browser_type, host, limit, offset)
            serializer = BrowserArtifactSerializer(cookies, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting browser cookies: {e}")
            return Response(
                {'error': 'Failed to retrieve browser cookies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='browser-downloads')
    def browser_downloads(self, request, pk=None):
        """Get browser downloads for case"""
        case = self.get_object()
        browser_type = request.query_params.get('browser_type')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))

        try:
            downloads = mongo_service.get_browser_downloads(case.case_id, browser_type, limit, offset)
            serializer = BrowserArtifactSerializer(downloads, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting browser downloads: {e}")
            return Response(
                {'error': 'Failed to retrieve browser downloads'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def registry(self, request, pk=None):
        """Get registry artifacts for case"""
        case = self.get_object()
        artifact_type = request.query_params.get('artifact_type')
        limit = int(request.query_params.get('limit', 200))
        offset = int(request.query_params.get('offset', 0))

        try:
            registry_artifacts = mongo_service.get_registry_artifacts(
                case.case_id, artifact_type, limit, offset
            )
            serializer = RegistryArtifactSerializer(registry_artifacts, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting registry artifacts: {e}")
            return Response(
                {'error': 'Failed to retrieve registry artifacts'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def usb_devices(self, request, pk=None):
        """Get USB devices for case"""
        case = self.get_object()
        
        try:
            devices = mongo_service.get_usb_devices(case.case_id)
            serializer = USBDeviceSerializer(devices, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting USB devices: {e}")
            return Response(
                {'error': 'Failed to retrieve USB devices'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='event-logs')
    def event_logs(self, request, pk=None):
        """Get event logs for case"""
        case = self.get_object()
        event_type = request.query_params.get('event_type')
        source_name = request.query_params.get('source_name')
        limit = int(request.query_params.get('limit', 200))
        offset = int(request.query_params.get('offset', 0))

        try:
            events = mongo_service.get_event_logs(case.case_id, event_type, source_name, limit, offset)
            serializer = EventLogArtifactSerializer(events, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting event logs: {e}")
            return Response(
                {'error': 'Failed to retrieve event logs'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def filesystem(self, request, pk=None):
        """Get filesystem artifacts for case"""
        case = self.get_object()
        artifact_type = request.query_params.get('artifact_type')
        limit = int(request.query_params.get('limit', 200))
        offset = int(request.query_params.get('offset', 0))

        try:
            artifacts = mongo_service.get_filesystem_artifacts(case.case_id, artifact_type, limit, offset)
            serializer = FileSystemArtifactSerializer(artifacts, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting filesystem artifacts: {e}")
            return Response(
                {'error': 'Failed to retrieve filesystem artifacts'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def android_artifacts(self, request, pk=None):
        """Get Android TAR artifacts for case"""
        case = self.get_object()
        artifact_type = request.query_params.get('artifact_type')
        package_name = request.query_params.get('package')
        limit = int(request.query_params.get('limit', 200))
        offset = int(request.query_params.get('offset', 0))

        try:
            artifacts = mongo_service.get_android_artifacts(
                case.case_id, artifact_type, package_name, limit, offset
            )
            serializer = AndroidArtifactSerializer(artifacts, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting Android artifacts: {e}")
            return Response(
                {'error': 'Failed to retrieve Android artifacts'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='ml-infer')
    def ml_infer(self, request, pk=None):
        """Run GAT inference and store top anomalies in MongoDB"""
        case = self.get_object()
        threshold = float(request.data.get('threshold', 0.5))
        top_n = int(request.data.get('top_n', 50))

        try:
            result = run_gat_inference(case.case_id, threshold=threshold, top_n=top_n)
            if not result.get("success"):
                return Response(
                    {'error': result.get('error', 'Inference failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            summary = {
                "total_activities": result.get("total_activities", 0),
                "anomalies_detected": result.get("anomalies_detected", 0),
                "threshold": result.get("threshold", threshold),
                "updated_at": datetime.now().isoformat(),
            }
            mongo_service.store_ml_anomalies(case.case_id, result.get("top_anomalies", []), summary=summary)

            total_activities = summary["total_activities"] or 0
            anomalies_detected = summary["anomalies_detected"] or 0
            anomaly_rate = (anomalies_detected / total_activities) if total_activities else 0
            if anomaly_rate >= 0.2:
                risk_level = "HIGH"
            elif anomaly_rate >= 0.1:
                risk_level = "MEDIUM"
            elif anomaly_rate > 0:
                risk_level = "LOW"
            else:
                risk_level = "MINIMAL"

            recommendations = []
            if risk_level in {"HIGH", "MEDIUM"}:
                recommendations.append("Review high-score anomalies immediately")
            if anomalies_detected == 0:
                recommendations.append("No anomalies detected; continue monitoring")

            return Response({
                'success': True,
                'case_id': case.case_id,
                'total_activities': total_activities,
                'anomalies_detected': anomalies_detected,
                'threshold': result.get("threshold", threshold),
                'top_anomalies': result.get("top_anomalies", []),
                'insights': {
                    'risk_assessment': {
                        'risk_level': risk_level,
                        'overall_risk_score': round(anomaly_rate * 100, 1),
                        'critical_indicators': (
                            ['High anomaly rate detected'] if anomaly_rate >= 0.2 else []
                        )
                    },
                    'recommendations': [r for r in recommendations if r]
                }
            })
        except Exception as e:
            logger.error(f"Error running ML inference: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to run ML inference'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='ml-anomalies')
    def ml_anomalies(self, request, pk=None):
        """Get stored ML anomalies for case"""
        case = self.get_object()
        min_score = request.query_params.get('min_score')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        try:
            items = mongo_service.get_ml_anomalies(case.case_id, min_score, limit, offset)
            serializer = MLAnomalySerializer(items, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting ML anomalies: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve ML anomalies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='android-ml-infer')
    def android_ml_infer(self, request, pk=None):
        """Run Android TabTransformer inference and store results"""
        case = self.get_object()
        threshold = float(request.data.get('threshold', 0.5))
        top_n = int(request.data.get('top_n', 50))
        csv_path = request.data.get('csv_path')

        if not csv_path:
            return Response(
                {'error': 'csv_path is required for Android inference'},
                status=status.HTTP_400_BAD_REQUEST
            )

        features_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'ai_ml',
            'android_selected_features.json'
        )
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'dl_models',
            'best_finetuned_model.pth.zip'
        )

        try:
            result = run_android_inference(
                csv_path=csv_path,
                features_path=features_path,
                model_path=model_path,
                threshold=threshold,
                top_n=top_n
            )
            if not result.get("success"):
                return Response(
                    {'error': result.get('error', 'Android inference failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            summary = {
                "total_samples": result.get("total_samples", 0),
                "threshold": result.get("threshold", threshold),
                "updated_at": datetime.now().isoformat(),
            }
            mongo_service.store_android_ml_anomalies(case.case_id, result.get("top_anomalies", []), summary=summary)

            return Response({
                'success': True,
                'case_id': case.case_id,
                'total_samples': result.get("total_samples", 0),
                'threshold': result.get("threshold", threshold),
                'top_anomalies': result.get("top_anomalies", []),
            })
        except Exception as e:
            logger.error(f"Error running Android ML inference: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to run Android ML inference'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='android-ml-anomalies')
    def android_ml_anomalies(self, request, pk=None):
        """Get stored Android ML anomalies for case"""
        case = self.get_object()
        min_score = request.query_params.get('min_score')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        try:
            items = mongo_service.get_android_ml_anomalies(case.case_id, min_score, limit, offset)
            serializer = AndroidMLAnomalySerializer(items, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting Android ML anomalies: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve Android ML anomalies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """Generate a simple case report entry (metadata only)."""
        case = self.get_object()
        report_format = request.data.get('format', 'json')
        now = datetime.now().isoformat()
        report_id = f"REPORT_{case.case_id}_{now.replace(':','').replace('-','').split('.')[0]}"

        report_entry = {
            "report_id": report_id,
            "format": report_format,
            "created_at": now,
            "status": "generated",
        }

        try:
            if report_format == "pdf":
                from .reporting import generate_case_report
                file_path, file_url, report_id, created_at = generate_case_report(case)
                report_entry.update({
                    "report_id": report_id,
                    "created_at": created_at,
                    "file_path": file_path,
                    "file_url": file_url,
                })

            mongo_service.storage.collections['cases'].update_one(
                {"case_id": case.case_id},
                {"$push": {"reports": report_entry}}
            )
            return Response({"success": True, "report": report_entry})
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        """List reports for a case (metadata)."""
        case = self.get_object()
        try:
            case_doc = mongo_service.get_case_info(case.case_id) or {}
            reports = case_doc.get("reports", [])
            return Response(reports)
        except Exception as e:
            logger.error(f"Error getting reports: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve reports'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='deleted-files')
    def deleted_files(self, request, pk=None):
        """Get deleted files for case"""
        case = self.get_object()
        filename_contains = request.query_params.get('filename')

        try:
            deleted = mongo_service.get_deleted_files(case.case_id, filename_contains)
            serializer = DeletedFileSerializer(deleted, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting deleted files: {e}")
            return Response(
                {'error': 'Failed to retrieve deleted files'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='installed-programs')
    def installed_programs(self, request, pk=None):
        """Get installed programs for case"""
        case = self.get_object()
        publisher = request.query_params.get('publisher')

        try:
            programs = mongo_service.get_installed_programs(case.case_id, publisher)
            serializer = InstalledProgramSerializer(programs, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting installed programs: {e}")
            return Response(
                {'error': 'Failed to retrieve installed programs'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='user-activity')
    def user_activity(self, request, pk=None):
        """Get user activity for case"""
        case = self.get_object()
        activity_type = request.query_params.get('activity_type')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        try:
            activity = mongo_service.get_user_activity(case.case_id, activity_type, limit, offset)
            serializer = UserActivitySerializer(activity, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return Response(
                {'error': 'Failed to retrieve user activity'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get timeline for case"""
        case = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        event_type = request.query_params.get('event_type')
        limit = int(request.query_params.get('limit', 200))
        offset = int(request.query_params.get('offset', 0))
        
        try:
            timeline = mongo_service.get_timeline(
                case.case_id, start_date, end_date, event_type, limit, offset
            )
            serializer = TimelineEventSerializer(timeline, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting timeline: {e}")
            return Response(
                {'error': 'Failed to retrieve timeline'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def search(self, request, pk=None):
        """Search artifacts for case"""
        case = self.get_object()
        search_term = request.query_params.get('q', '')
        collections = request.query_params.getlist('collections')
        
        if not search_term:
            return Response(
                {'error': 'Search term is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_time = datetime.now()
            results = mongo_service.search_artifacts(case.case_id, search_term, collections or None)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Count total results
            total_results = sum(len(artifacts) for artifacts in results.values())
            
            # Log search query
            SearchQuery.objects.create(
                user=request.user,
                case=case,
                query_text=search_term,
                query_type='case_search',
                filters={'collections': collections},
                results_count=total_results,
                execution_time=execution_time
            )
            
            serializer = SearchResultsSerializer({
                'query': search_term,
                'total_results': total_results,
                'execution_time': execution_time,
                'results': results
            })
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return Response(
                {'error': 'Failed to search artifacts'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def suspicious_activity(self, request, pk=None):
        """Get suspicious activity indicators"""
        case = self.get_object()
        
        try:
            indicators = mongo_service.get_suspicious_activity(case.case_id)
            return Response({'indicators': indicators})
        except Exception as e:
            logger.error(f"Error getting suspicious activity: {e}")
            return Response(
                {'error': 'Failed to retrieve suspicious activity'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def behavior_analysis(self, request, pk=None):
        """Get user behavior analysis"""
        case = self.get_object()
        
        try:
            analysis = mongo_service.get_user_behavior_analysis(case.case_id)
            return Response(analysis)
        except Exception as e:
            logger.error(f"Error getting behavior analysis: {e}")
            return Response(
                {'error': 'Failed to retrieve behavior analysis'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def network_analysis(self, request, pk=None):
        """Get network analysis"""
        case = self.get_object()
        
        try:
            analysis = mongo_service.get_network_analysis(case.case_id)
            return Response(analysis)
        except Exception as e:
            logger.error(f"Error getting network analysis: {e}")
            return Response(
                {'error': 'Failed to retrieve network analysis'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def re_extract(self, request, pk=None):
        """Re-extract artifacts from the disk image"""
        case = self.get_object()
        
        if not case.image_path or not os.path.exists(case.image_path):
            return Response(
                {'error': 'Disk image not found for this case'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if there's already a running extraction job
        running_job = ExtractionJob.objects.filter(
            case=case,
            status__in=['queued', 'running']
        ).first()
        
        if running_job:
            return Response(
                {'error': 'An extraction job is already running for this case'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new extraction job
        job = ExtractionJob.objects.create(
            case=case,
            source_path=case.image_path,
            status='queued'
        )
        
        # Start processing in background
        self._start_processing(case, job, case.image_path)
        
        return Response({
            'message': 'Re-extraction started',
            'job_id': job.id,
            'status': 'queued'
        }, status=status.HTTP_202_ACCEPTED)


class CaseNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for case notes"""
    
    serializer_class = CaseNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get notes for specific case"""
        case_id = self.request.query_params.get('case_id')
        if case_id:
            return CaseNote.objects.filter(case__case_id=case_id)
        return CaseNote.objects.all()
    
    def perform_create(self, serializer):
        """Create a new note"""
        note = serializer.save()
        log_audit_action(
            self.request.user, 'create', 'note', str(note.id),
            {'case_id': note.case.case_id, 'title': note.title}, self.request
        )


class CaseFileViewSet(viewsets.ModelViewSet):
    """ViewSet for case files"""
    
    serializer_class = CaseFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get files for specific case"""
        case_id = self.request.query_params.get('case_id')
        if case_id:
            return CaseFile.objects.filter(case__case_id=case_id)
        return CaseFile.objects.all()
    
    def perform_create(self, serializer):
        """Create a new file"""
        file_obj = serializer.save()
        log_audit_action(
            self.request.user, 'create', 'file', str(file_obj.id),
            {'case_id': file_obj.case.case_id, 'name': file_obj.name}, self.request
        )


class ExtractionJobViewSet(viewsets.ModelViewSet):
    """ViewSet for extraction jobs"""
    
    serializer_class = ExtractionJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get extraction jobs"""
        case_id = self.request.query_params.get('case_id')
        if case_id:
            return ExtractionJob.objects.filter(case__case_id=case_id)
        return ExtractionJob.objects.all()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an extraction job"""
        job = self.get_object()
        if job.status in ['queued', 'running']:
            job.status = 'cancelled'
            job.save()
            return Response({'status': 'cancelled'})
        else:
            return Response(
                {'error': 'Job cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profiles"""
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user profiles"""
        return UserProfile.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SearchQueryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for search queries (read-only)"""
    
    serializer_class = SearchQuerySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get search queries for current user"""
        return SearchQuery.objects.filter(user=self.request.user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit logs (read-only)"""
    
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get audit logs"""
        queryset = AuditLog.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by resource type
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


# API View for disk images
from rest_framework.views import APIView


class DiskImagesView(APIView):
    """View to list available disk images"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get list of available disk images from data/samples"""
        try:
            images = get_available_disk_images()
            return Response({
                'count': len(images),
                'images': images
            })
        except Exception as e:
            logger.error(f"Error listing disk images: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to list disk images'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
