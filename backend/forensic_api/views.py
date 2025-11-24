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
    SearchResultsSerializer, StatisticsSerializer
)
from .mongodb_service import mongo_service
from .utils import log_audit_action, get_client_ip

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class ForensicCaseViewSet(viewsets.ModelViewSet):
    """ViewSet for forensic cases"""
    
    serializer_class = ForensicCaseSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
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
    
    def perform_create(self, serializer):
        """Create a new case"""
        case = serializer.save()
        log_audit_action(
            self.request.user, 'create', 'case', case.case_id,
            {'title': case.title}, self.request
        )
    
    def perform_update(self, serializer):
        """Update a case"""
        case = serializer.save()
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
    
    @action(detail=True, methods=['get'])
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
    
    @action(detail=True, methods=['get'])
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