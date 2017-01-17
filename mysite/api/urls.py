"""
Root API URLs.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""
from django.conf.urls import url, include

urlpatterns = [
    url(r'^v0/', include('api.v0.urls', namespace='v0')),
]
