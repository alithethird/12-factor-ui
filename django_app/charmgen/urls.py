from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/validate-source/', views.validate_source, name='validate_source'),
    
    # --- NEW SSE Endpoints ---
    path('api/start-generation/', views.start_generation_task, name='start_generation'),
    path('api/generation-status/<str:task_id>/', views.generation_status, name='generation_status'),
    path('api/download-bundle/<str:task_id>/', views.download_bundle, name='download_bundle'),

    # Frontend view
    path('', views.index, name='index'),
]
