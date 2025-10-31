
import flet as ft
# Import state management
from state import TEMP_STORAGE_PATH
from ui.ConfigOptions import ConfigOptions
from ui.GenerateFiles import GenerateFiles
# Import UI components
from ui.SelectFramework import SelectFramework
from ui.SelectIntegrations import SelectIntegrations
from ui.UploadCode import UploadCode


def main(page: ft.Page):
    page.title = "12 Factory"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1250
    page.window.height = 800
    page.scroll = ft.ScrollMode.ADAPTIVE

    # --- Application State ---
    # This dictionary is passed down to all components
    app_state = {
        "active_step": 1,
        "form_data": {
            "framework": "",
            "frameworkName": "",
            "source": None,
            "jobId": "",
            "integrations": [],
            "configOptions": [],
            "sourceProjectName": "",
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
        # Handle project name extraction centrally
        if "source" in new_data and new_data["source"]:
            app_state["form_data"]["sourceProjectName"] = new_data["source"].get(
                "projectName"
            ).replace(" ", "_").replace("-", "_").lower()
        page.update()

    # --- Main Layout ---
    # Create instances of all the step components
    steps = [
        SelectFramework(app_state),
        UploadCode(app_state),
        SelectIntegrations(app_state),
        ConfigOptions(app_state),
        GenerateFiles(app_state),
    ]

    page.add(
        ft.Container(
            content=ft.Column(
                steps,
                spacing=10,
            ),
            padding=20,
        )
    )


if __name__ == "__main__":
    # Ensure the main temp directory for our app exists on startup
    if not TEMP_STORAGE_PATH.exists():
        TEMP_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    ft.app(target=main, assets_dir="assets")

    # Clean up the main temp directory on exit (optional)
    # Be careful with this in production if multiple instances might run
    # if TEMP_STORAGE_PATH.exists():
    #     print(f"Cleaning up {TEMP_STORAGE_PATH}...")
    #     shutil.rmtree(TEMP_STORAGE_PATH)
