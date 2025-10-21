import flet as ft
import os
import shutil
import threading
import time
import uuid
from pathlib import Path

# Import your existing logic modules
from logic.downloader import GithubDownloader
from logic.extractor import ArchiveExtractor
from logic.processor import ApplicationProcessor
from logic.rockcraft import RockcraftGenerator
from logic.charmcraft import CharmcraftGenerator
from logic.bundler import BundleArtifacts

# Import the new UI components
from ui.AccordionStep import AccordionStep
from ui.SelectFramework import SelectFramework

# --- App State Management ---
JOB_STORE = {}
TEMP_STORAGE_PATH = Path("temp_jobs")


def main(page: ft.Page):
    page.title = "Rock & Charm Generator"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 800
    page.scroll = ft.ScrollMode.ADAPTIVE

    # --- Application State ---
    app_state = {
        "active_step": 1,
        "form_data": {
            "framework": "", "frameworkName": "",
            "source": None, "jobId": "", "integrations": [],
            "configOptions": [], "sourceProjectName": ""
        },
        "set_active_step": lambda step: set_step(step),
        "update_form_data": lambda data: update_data(data),
        "get_form_data": lambda: app_state["form_data"],
        "page": page,
    }

    # --- UI Update Logic ---
    def set_step(step_number):
        app_state["active_step"] = step_number
        page.update()

    def update_data(new_data):
        app_state["form_data"].update(new_data)
        if "source" in new_data and new_data["source"]:
             app_state["form_data"]["sourceProjectName"] = new_data["source"].get("projectName")
        page.update()

    # --- Step Content Definitions (for steps not yet refactored) ---

    def build_step2():
        repo_url_field = ft.TextField(label="GitHub Repository URL", hint_text="https://github.com/user/repo")
        file_picker = ft.FilePicker(on_result=lambda e: on_file_picked(e))
        page.overlay.append(file_picker) # Add file picker to overlay
        file_picker_button = ft.ElevatedButton("Select Archive...", on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["zip", "tar", "gz"]))
        selected_file_text = ft.Text("No file selected.")

        github_view = ft.Column([repo_url_field], visible=True)
        upload_view = ft.Column([file_picker_button, selected_file_text], visible=False)

        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files:
                selected_file_text.value = f"Selected: {e.files[0].name}"
                selected_file_text.data = e.files[0]
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
            job_dir.mkdir(parents=True, exist_ok=True)
            
            project_path = ""
            project_name = ""
            source_info = {}

            try:
                time.sleep(1) # Simulate work
                if tabs.selected_index == 0:
                    downloader = GithubDownloader(repo_url_field.value)
                    result = downloader.download(str(job_dir))
                    project_path = result['path']
                    project_name = result['project_name']
                    source_info = {"type": "github", "projectName": project_name}
                else:
                    file_data = selected_file_text.data
                    if not file_data:
                        raise ValueError("No file selected for upload.")
                    extractor = ArchiveExtractor(file_data.path, file_data.name)
                    result = extractor.extract(str(job_dir))
                    project_path = result['root_path']
                    project_name = result['project_name']
                    source_info = {"type": "upload", "projectName": project_name}
                
                processor = ApplicationProcessor(project_path, app_state["form_data"]["framework"])
                processor.check_project()

                JOB_STORE[job_id] = project_path
                app_state["update_form_data"]({"jobId": job_id, "source": source_info})
                accordion2.update_summary(f"Source: {project_name}")
                app_state["set_active_step"](3)

            except Exception as ex:
                error_text.value = f"Error: {ex}"
                error_text.visible = True
                shutil.rmtree(job_dir, ignore_errors=True)
            finally:
                progress_ring.visible = False
                page.update()

        return ft.Column([
            tabs, github_view, upload_view,
            ft.ElevatedButton("Validate & Continue", on_click=on_validate, icon=ft.Icons.CHECK),
            progress_ring, error_text
        ], spacing=15)

    def build_step5():
        log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        log_container = ft.Container(
            content=log_view,
            border=ft.border.all(1, ft.Colors.BLACK26),
            border_radius=5, padding=10, height=300,
            visible=False, bgcolor=ft.Colors.BLACK12,
        )
        save_picker = ft.FilePicker(on_result=lambda e: on_save_dialog_result(e))
        page.overlay.append(save_picker)

        def on_save_dialog_result(e: ft.FilePickerResultEvent):
            zip_path = e.control.data
            if not e.path or not zip_path:
                return
            try:
                shutil.move(zip_path, e.path)
                update_status("Bundle saved successfully!")
            except Exception as ex:
                update_status(f"Error saving file: {ex}")

        def update_status(message, is_log=False):
            if is_log:
                log_view.controls.append(ft.Text(message, font_family="monospace", size=12))
            else:
                page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                page.snack_bar.open = True
            page.update()

        def run_generation_in_thread():
            try:
                data = app_state["get_form_data"]()
                project_path = JOB_STORE.get(data["jobId"])
                
                if not project_path: raise ValueError("Job not found or expired.")

                rock_gen = RockcraftGenerator(project_path)
                rock_file_path = rock_gen.generate(status_callback=update_status)

                charm_gen = CharmcraftGenerator(
                    data["integrations"], data["configOptions"], data["sourceProjectName"]
                )
                charm_file_path, charm_cleanup = charm_gen.generate(status_callback=update_status)
                
                update_status("Bundling artifacts...")
                zip_path, zip_cleanup = BundleArtifacts(rock_file_path, charm_file_path)

                save_picker.data = zip_path
                save_picker.save_file(dialog_title="Save Your Bundle", file_name="rock-and-charm-bundle.zip")
                
                if data["jobId"] in JOB_STORE:
                    shutil.rmtree(TEMP_STORAGE_PATH / data["jobId"], ignore_errors=True)
                    del JOB_STORE[data["jobId"]]
                charm_cleanup()
                
            except Exception as e:
                update_status(f"ERROR: {e}", is_log=True)
            finally:
                generate_button.disabled = False
                page.update()

        def on_generate(e):
            log_container.visible = True
            log_view.controls.clear()
            log_view.controls.append(ft.Text("Starting generation...", weight=ft.FontWeight.BOLD))
            generate_button.disabled = True
            page.update()
            
            thread = threading.Thread(target=run_generation_in_thread, daemon=True)
            thread.start()

        generate_button = ft.ElevatedButton("Generate & Save Bundle", on_click=on_generate, icon=ft.Icons.SAVE)
        
        return ft.Column([
            ft.Text("All steps complete. You can now generate your files.", size=16),
            generate_button, log_container,
        ], spacing=15)
    
    # --- Main Layout ---
    accordion1 = SelectFramework(app_state)
    accordion2 = AccordionStep("2. Provide Source Code", 2, app_state, build_step2())
    accordion3 = AccordionStep("3. Select Integrations", 3, app_state, ft.Text("Integrations UI would go here."))
    accordion4 = AccordionStep("4. Custom Config Options", 4, app_state, ft.Text("Config Options UI would go here."))
    accordion5 = AccordionStep("5. Generate Files", 5, app_state, build_step5())

    page.add(
        ft.Container(
            content=ft.Column(
                [accordion1, accordion2, accordion3, accordion4, accordion5],
                spacing=10
            ),
            padding=20,
        )
    )

if __name__ == "__main__":
    if not TEMP_STORAGE_PATH.exists():
        TEMP_STORAGE_PATH.mkdir()

    ft.app(target=main, assets_dir="static")

    if TEMP_STORAGE_PATH.exists():
        shutil.rmtree(TEMP_STORAGE_PATH)

