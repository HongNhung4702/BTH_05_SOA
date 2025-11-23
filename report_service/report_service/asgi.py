"""
ASGI config for report_service project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_service.settings')

application = get_asgi_application()

