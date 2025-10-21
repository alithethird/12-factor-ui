import flet as ft
import shutil
import time
import uuid

from .AccordionStep import AccordionStep
from logic.downloader import GithubDownloader
from logic.extractor import ArchiveExtractor
from logic.processor import ApplicationProcessor
# Import from the new state management file
from state import TEMP_STORAGE_PATH, JOB_STORE

class UploadCode(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        page = self.app_state["page"]

        # --- Define Controls for this step ---
        repo_url_field = ft.TextField(label="GitHub Repository URL", hint_text="https://github.com/user/repo")
        
        # The FilePicker needs to be in the page's overlay
        file_picker = ft.FilePicker(on_result=lambda e: on_file_picked(e))
        page.overlay.append(file_picker)
        
        file_picker_button = ft.ElevatedButton(
            "Select Archive...",
            on_click=lambda _: file_picker.pick_files(
                allow_multiple=False, allowed_extensions=["zip", "tar", "gz"]
            ),
        )
        selected_file_text = ft.Text("No file selected.")

        github_view = ft.Column([repo_url_field], visible=True)
        upload_view = ft.Column([file_picker_button, selected_file_text], visible=False)

        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files:
                selected_file_text.value = f"Selected: {e.files[0].name}"
                selected_file_text.data = e.files[0]  # Store the FilePickerFile object
            else:
                selected_file_text.value = "No file selected."
            page.update()

        def switch_tabs(e):
            is_github = e.control.selected_index == 0
            github_view.visible = is_github
            upload_view.visible = not is_github
            page.update()

        tabs = ft.Tabs(
            selected_index=0,
            on_change=switch_tabs,
            tabs=[ft.Tab(text="From GitHub"), ft.Tab(text="Upload Archive")],
        )

        progress_ring = ft.ProgressRing(visible=False)
        error_text = ft.Text(color=ft.Colors.RED, visible=False)

        def on_validate(e):
            progress_ring.visible = True
            error_text.visible = False
            page.update()

            job_id = str(uuid.uuid4())
            job_dir = TEMP_STORAGE_PATH / job_id
            print(f"{job_dir=}")
            job_dir.mkdir(parents=True, exist_ok=True)

            project_path = ""
            project_name = ""
            source_info = {}

            try:
                if tabs.selected_index == 0:
                    downloader = GithubDownloader(repo_url_field.value)
                    result = downloader.download(str(job_dir))
                    project_path = result["path"]
                    project_name = result["project_name"]
                    source_info = {"type": "github", "projectName": project_name}
                else:
                    file_data = selected_file_text.data
                    if not file_data:
                        raise ValueError("No file selected for upload.")
                    extractor = ArchiveExtractor(file_data.path, file_data.name)
                    result = extractor.extract(str(job_dir))
                    project_path = result["root_path"]
                    project_name = result["project_name"]
                    source_info = {"type": "upload", "projectName": project_name}

                processor = ApplicationProcessor(
                    project_path, self.app_state["form_data"]["framework"]
                )
                processor.check_project()

                JOB_STORE[job_id] = project_path
                self.app_state["update_form_data"]({"jobId": job_id, "source": source_info})
                self.update_summary(f"Source: {project_name}")
                self.app_state["set_active_step"](3)

            except Exception as ex:
                error_text.value = f"Error: {ex}"
                error_text.visible = True
                shutil.rmtree(job_dir, ignore_errors=True)
            finally:
                progress_ring.visible = False
                page.update()

        content_control = ft.Column(
            [
                tabs,
                github_view,
                upload_view,
                ft.ElevatedButton(
                    "Validate & Continue", on_click=on_validate, icon=ft.Icons.CHECK
                ),
                progress_ring,
                error_text,
            ],
            spacing=15,
        )

        # Call the parent constructor
        super().__init__(
            title="2. Provide Source Code",
            step_number=2,
            app_state=app_state,
            content_control=content_control,
        )
