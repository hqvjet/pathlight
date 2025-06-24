import sys
import os

# Add libs path to use shared models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs', 'common-types-py'))

# Import shared User model
from shared_models import User

# Make shared User model available
__all__ = ['User']

# Note: UserProfile is now merged into User model in shared_models.py
# All user profile data is now stored in the unified users table
# No need for separate UserProfile class
