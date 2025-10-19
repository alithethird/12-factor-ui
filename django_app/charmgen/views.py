from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
import json
import uuid
import os
import shutil
import time
import threading
import subprocess # Import subprocess for exception handling

from .logic.downloader import GithubDownloader
from .logic.extractor import ArchiveExtractor
from .logic.processor import ApplicationProcessor
from .logic.rockcraft import RockcraftGenerator
from .logic.charmcraft import CharmcraftGenerator
from .logic.bundler import BundleArtifacts
from generator_project.settings import JOB_STORAGE_PATH

# Simple in-memory stores for a dev environment.
JOB_STORE = {}
TASK_STATUS = {}
FINAL_FILES = {}

def index(request):
    """Serves the main index.html page."""
    return render(request, 'charmgen/index.html')

@api_view(['POST'])
def validate_source(request):
    """
    Handles source code validation from GitHub or file upload.
    Stores the validated project in a temporary location and returns a job ID.
    """
    framework = request.POST.get('framework')
    project_path = ""
    project_name = ""

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOB_STORAGE_PATH, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            extractor = ArchiveExtractor(uploaded_file)
            result = extractor.extract(job_dir)
            project_path = result['root_path']
            project_name = result['project_name']
        else:
            data = json.loads(request.body)
            repo_url = data.get('repoUrl')
            if not repo_url:
                return HttpResponseBadRequest("Missing repoUrl")
            downloader = GithubDownloader(repo_url)
            result = downloader.download(job_dir)
            project_path = result['path']
            project_name = result['project_name']

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


# --- NEW BACKGROUND TASK LOGIC ---

def run_generation_task(task_id, form_data):
    """This function runs in a background thread."""
    def update_status(message, is_log=False):
        # Store the message with a type ('status' or 'log')
        TASK_STATUS[task_id]['messages'].append({'text': message, 'type': 'log' if is_log else 'status'})

    try:
        job_id = form_data.get('jobId')
        project_path = JOB_STORE.get(job_id)
        if not project_path:
            raise ValueError("Job not found or expired.")
        
        update_status("Starting Rock generation...")
        rock_gen = RockcraftGenerator(project_path)
        rock_file_path = rock_gen.generate(status_callback=update_status)

        update_status("Starting Charm generation...")
        charm_gen = CharmcraftGenerator(
            form_data.get('integrations', []),
            form_data.get('configOptions', []),
            form_data.get('sourceProjectName', 'my-charm')
        )
        charm_file_path, charm_cleanup = charm_gen.generate(status_callback=update_status)
        update_status("Charm generation complete.")
        
        update_status("Bundling artifacts...")
        zip_path, zip_cleanup = BundleArtifacts(rock_file_path, charm_file_path)
        update_status("Bundle created.")

        FINAL_FILES[task_id] = {'path': zip_path, 'cleanup': [charm_cleanup, zip_cleanup]}
        TASK_STATUS[task_id]['done'] = True
        
        if job_id in JOB_STORE:
            shutil.rmtree(os.path.join(JOB_STORAGE_PATH, job_id), ignore_errors=True)
            del JOB_STORE[job_id]
    
    except subprocess.CalledProcessError as e:
        # Handle errors from shell commands specifically
        error_message = f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}."
        print(f"Error in task {task_id}: {error_message}")
        TASK_STATUS[task_id]['error'] = error_message
        TASK_STATUS[task_id]['done'] = True
    except Exception as e:
        print(f"Error in task {task_id}: {e}")
        TASK_STATUS[task_id]['error'] = str(e)
        TASK_STATUS[task_id]['done'] = True

@api_view(['POST'])
def start_generation_task(request):
    """Starts the generation process in a background thread and returns a task ID."""
    task_id = str(uuid.uuid4())
    form_data = json.loads(request.body)
    
    TASK_STATUS[task_id] = {
        'done': False,
        'messages': [],
        'error': None
    }
    
    thread = threading.Thread(target=run_generation_task, args=(task_id, form_data))
    thread.start()
    
    return JsonResponse({'success': True, 'taskId': task_id})

def generation_status(request, task_id):
    """This view streams status updates using Server-Sent Events."""
    def event_stream():
        last_sent_index = 0
        while True:
            if task_id not in TASK_STATUS:
                break

            task = TASK_STATUS[task_id]
            
            # Send any new messages
            for i in range(last_sent_index, len(task['messages'])):
                message_obj = task['messages'][i]
                # Pass the full object {'text': '...', 'type': '...'}
                data = json.dumps(message_obj)
                yield f"data: {data}\n\n"
            last_sent_index = len(task['messages'])
            
            if task['done']:
                if task['error']:
                    data = json.dumps({'error': task['error']})
                    yield f"data: {data}\n\n"
                else:
                    download_url = request.build_absolute_uri(f'/api/download-bundle/{task_id}/')
                    data = json.dumps({'downloadUrl': download_url})
                    yield f"data: {data}\n\n"
                break
            
            time.sleep(1)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def download_bundle(request, task_id):
    """Serves the final generated zip file for download."""
    file_info = FINAL_FILES.get(task_id)
    if not file_info:
        return HttpResponseBadRequest("File not found or task expired.")

    try:
        response = FileResponse(open(file_info['path'], 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="rock-and-charm-bundle.zip"'
        return response
    finally:
        for cleanup_func in file_info['cleanup']:
            cleanup_func()
        if task_id in FINAL_FILES:
            del FINAL_FILES[task_id]

