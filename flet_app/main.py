import shutil
import threading

import flet as ft
from logic.bundler import BundleArtifacts
from logic.charmcraft import CharmcraftGenerator
# Import your existing logic modules
from logic.rockcraft import RockcraftGenerator
# Import from the new state management file
from state import JOB_STORE, TEMP_STORAGE_PATH
# Import the new UI components
from ui.AccordionStep import AccordionStep
from ui.ConfigOptions import ConfigOptions
from ui.SelectFramework import SelectFramework
from ui.SelectIntegrations import SelectIntegrations
from ui.UploadCode import UploadCode


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
        "get_framework": lambda: app_state["form_data"].get("framework"),
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

                rock_gen = RockcraftGenerator(project_path, app_state["get_framework"]())
                rock_file_path = rock_gen.generate(status_callback=update_status)

                # Convert ConfigOption objects to dictionaries for CharmcraftGenerator
                config_options_dicts = [opt.to_dict() for opt in data["configOptions"]]
                integration_ids = [integ['id'] for integ in data["integrations"]]

                charm_gen = CharmcraftGenerator(
                    integration_ids, config_options_dicts, data["sourceProjectName"]
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
    accordion2 = UploadCode(app_state)
    accordion3 = SelectIntegrations(app_state)
    accordion4 = ConfigOptions(app_state)
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
    # Ensure the main temp directory for our app exists on startup
    if not TEMP_STORAGE_PATH.exists():
        TEMP_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    ft.app(target=main, assets_dir="assets")

    # The individual job folders are cleaned up as they are used,
    # so we no longer need a global cleanup here.

