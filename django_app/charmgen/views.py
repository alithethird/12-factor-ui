from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
import json
import uuid
import os
import shutil

from .logic.downloader import GithubDownloader
from .logic.extractor import ArchiveExtractor
from .logic.processor import ApplicationProcessor
from .logic.rockcraft import RockcraftGenerator
from .logic.charmcraft import CharmcraftGenerator
from .logic.bundler import BundleArtifacts
from generator_project.settings import JOB_STORAGE_PATH

# A simple in-memory store for jobs.
JOB_STORE = {}

def index(request):
    """Serves the main index.html page."""
    # No context data is needed anymore
    return render(request, 'charmgen/index.html')


@api_view(['POST'])
def validate_source(request):
    # ... (This function remains unchanged)
    framework = request.POST.get('framework')
    project_path = ""
    project_name = ""

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOB_STORAGE_PATH, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        # Handle file upload
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            extractor = ArchiveExtractor(uploaded_file)
            result = extractor.extract(job_dir)
            project_path = result['root_path']
            project_name = result['project_name']
        # Handle GitHub URL
        else:
            data = json.loads(request.body)
            repo_url = data.get('repoUrl')
            if not repo_url:
                return HttpResponseBadRequest("Missing repoUrl")
            downloader = GithubDownloader(repo_url)
            result = downloader.download(job_dir)
            project_path = result['path']
            project_name = result['project_name']

        # Validate the project
        processor = ApplicationProcessor(project_path, framework)
        processor.check_project()

        JOB_STORE[job_id] = project_path
        return JsonResponse({
            'success': True,
            'jobId': job_id,
            'projectName': project_name,
        })

    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['POST'])
def generate_bundle(request):
    # ... (This function remains unchanged)
    data = json.loads(request.body)
    job_id = data.get('jobId')
    project_path = JOB_STORE.get(job_id)

    if not project_path:
        return JsonResponse({'success': False, 'error': 'Job not found or expired.'}, status=404)

    try:
        # 1. Generate Rock
        rock_gen = RockcraftGenerator(project_path)
        rock_file_path = rock_gen.generate()

        # 2. Generate Charm
        charm_gen = CharmcraftGenerator(
            data.get('integrations', []),
            data.get('configOptions', []),
            data.get('sourceProjectName', 'my-charm')
        )
        charm_file_path, charm_cleanup = charm_gen.generate()

        # 3. Bundle files into a zip
        zip_path, zip_cleanup = BundleArtifacts(rock_file_path, charm_file_path)

        # 4. Stream the zip file to the client
        response = FileResponse(open(zip_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="rock-and-charm-bundle.zip"'
        
        return response

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    finally:
        # Cleanup all temporary files and directories
        if job_id in JOB_STORE:
            shutil.rmtree(os.path.join(JOB_STORAGE_PATH, job_id), ignore_errors=True)
            del JOB_STORE[job_id]
        if 'charm_cleanup' in locals():
            charm_cleanup()
        if 'zip_cleanup' in locals():
            zip_cleanup()
