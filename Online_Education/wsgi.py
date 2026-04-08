"""
WSGI config for Online_Education project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Online_Education.settings')

application = get_wsgi_application()