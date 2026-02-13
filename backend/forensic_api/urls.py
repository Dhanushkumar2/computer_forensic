"""
URL configuration for forensic API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'cases', views.ForensicCaseViewSet, basename='forensiccase')
router.register(r'notes', views.CaseNoteViewSet, basename='casenote')
router.register(r'files', views.CaseFileViewSet, basename='casefile')
router.register(r'jobs', views.ExtractionJobViewSet, basename='extractionjob')
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')
router.register(r'searches', views.SearchQueryViewSet, basename='searchquery')
router.register(r'audit', views.AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
    path('disk-images/', views.DiskImagesView.as_view(), name='disk-images'),
]