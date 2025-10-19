from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/validate-source/', views.validate_source, name='validate_source'),
    path('api/generate-bundle/', views.generate_bundle, name='generate_bundle'),

    # Frontend view
    path('', views.index, name='index'),
]
