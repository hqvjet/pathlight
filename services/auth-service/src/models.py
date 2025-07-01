import sys
import os

# Add libs path to use shared models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs', 'common-types-py'))

# Import shared models directly - no need to redefine them
from shared_models import User, Admin, TokenBlacklist, SharedBase

# Make all models available for import
__all__ = ['User', 'Admin', 'TokenBlacklist', 'SharedBase']
