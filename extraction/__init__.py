"""
Forensic Artifact Extraction Module

This module provides comprehensive forensic artifact extraction capabilities
for Windows systems from disk images.

Available extractors:
- BrowserArtifacts: Firefox, Chrome, Edge, Internet Explorer artifacts
- RegistryArtifacts: USB history, UserAssist, installed programs, run keys
- RecycleBinArtifacts: Deleted files and recycle bin analysis
- EventLogArtifacts: Windows event logs (.evt format)
- FileSystemArtifacts: Prefetch, link files, jump lists
- ForensicExtractor: Main orchestrator for all extraction modules
"""

from .browser_artifacts import BrowserArtifacts
from .registry_artifacts import RegistryArtifacts
from .recycle_bin import RecycleBinArtifacts
from .event_logs import EventLogArtifacts
from .filesystem_artifacts import FileSystemArtifacts
from .forensic_extractor import ForensicExtractor

__all__ = [
    'BrowserArtifacts',
    'RegistryArtifacts', 
    'RecycleBinArtifacts',
    'EventLogArtifacts',
    'FileSystemArtifacts',
    'ForensicExtractor'
]