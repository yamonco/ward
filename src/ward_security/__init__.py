"""
Ward Security System v2.0
Enterprise-grade file system protection with AI collaboration features
"""

__version__ = "2.0.0"
__author__ = "Ward Security Team"
__email__ = "security@ward-security.com"
__license__ = "MIT"

from .cli import main
from .installer import WardInstaller
from .deployer import WardDeployer

__all__ = [
    "main",
    "WardInstaller",
    "WardDeployer",
    "__version__"
]