import flet as ft
from .AccordionStep import AccordionStep  # Corrected import path
import shutil
import threading
import time
from pathlib import Path
import os  # Import os

# Import logic modules
from logic.rockcraft import RockcraftGenerator
from logic.charmcraft import CharmcraftGenerator
from logic.bundler import BundleArtifacts

# Import state
from state import TEMP_STORAGE_PATH, JOB_STORE
import logging
import flet as ft
from datetime import datetime

# --- Configuration ---
# Set the basic configuration for logging
logging.basicConfig(
    level=logging.INFO,  # Set the minimum level to log (e.g., DEBUG, INFO, WARNING, ERROR)
    format="%(asctime)s - %(levelname)s - %(message)s",
    # Customize the date/time format
    datefmt="%H:%M:%S.%f"[
        :-3
    ],  # Example format: HH:MM:SS.ms (removes the last 3 digits for precision)
)


class GenerateFiles(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]

        # --- State specific to this step ---
        self._generated_zip_path = None
        self._zip_cleanup_func = None
        self._rockcraft_yaml_path = None
        self._rock_file_path = None
        self._charmcraft_yaml_path = None  # NEW
        self._charm_file_path = None  # NEW
        self._charm_cleanup_func = None  # To store charm temp dir cleanup

        # --- UI Controls ---
        self.log_view = ft.Markdown(
            "",
            selectable=True,
            expand=True,
            extension_set=ft.MarkdownExtensionSet.COMMON_MARK,
            auto_follow_links=False,
        )
        self.log_scroll_column = ft.Column(
            [self.log_view], scroll=ft.ScrollMode.ALWAYS, expand=True
        )
        self.log_container = ft.Container(
            content=self.log_scroll_column,
            border=ft.border.all(1, ft.Colors.BLACK26),
            border_radius=5,
            padding=10,
            height=300,
            visible=False,
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )
        self.save_picker = ft.FilePicker(on_result=self.on_save_dialog_result)
        self.page.overlay.append(self.save_picker)

        # --- Buttons (Reordered and Renamed) ---
        self.init_rock_button = ft.ElevatedButton(  # Was generate_button
            "1. Init Rock", on_click=self.on_init_rock, icon=ft.Icons.PLAY_ARROW_ROUNDED
        )
        self.edit_rock_button = ft.ElevatedButton(
            "2. Edit Rock (Opt.)",
            on_click=self.on_edit_rockcraft,
            icon=ft.Icons.EDIT,
            disabled=True,
            visible=False,
        )
        self.pack_rock_init_charm_button = ft.ElevatedButton(  # Was pack_rock_button
            "3. Pack Rock & Init Charm",
            on_click=self.on_pack_rock_init_charm,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=True,
            visible=False,
        )
        self.edit_charm_button = ft.ElevatedButton(  # NEW
            "4. Edit Charm (Opt.)",
            on_click=self.on_edit_charmcraft,
            icon=ft.Icons.EDIT,
            disabled=True,
            visible=False,
        )
        self.pack_charm_bundle_button = ft.ElevatedButton(  # NEW
            "5. Pack Charm & Bundle",
            on_click=self.on_pack_charm_and_bundle,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=True,
            visible=False,
        )
        self.save_bundle_button = ft.ElevatedButton(  # Was save_button
            "6. Save Bundle",
            on_click=self.on_save_bundle,
            icon=ft.Icons.SAVE,
            disabled=True,
            visible=False,
        )

        # --- Modals ---
        self.rock_yaml_editor = ft.TextField(
            multiline=True, expand=True, min_lines=15  # font_family="monospace",
        )
        self.rock_edit_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit rockcraft.yaml"),
            content=ft.Container(
                self.rock_yaml_editor, padding=ft.padding.symmetric(vertical=10)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self.on_cancel_rock_yaml),
                ft.TextButton("Save", on_click=self.on_save_rock_yaml),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(self.rock_edit_modal)

        self.charm_yaml_editor = ft.TextField(
            multiline=True, expand=True, min_lines=15  # font_family="monospace",
        )  # NEW
        self.charm_edit_modal = ft.AlertDialog(  # NEW
            modal=True,
            title=ft.Text("Edit charmcraft.yaml"),
            content=ft.Container(
                self.charm_yaml_editor, padding=ft.padding.symmetric(vertical=10)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self.on_cancel_charm_yaml),
                ft.TextButton("Save", on_click=self.on_save_charm_yaml),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(self.charm_edit_modal)

        # --- Layout ---
        content_control = ft.Column(
            [
                ft.Text(
                    "All steps complete. You can now generate your files.", size=16
                ),
                ft.Row(  # Arrange buttons horizontally
                    [
                        self.init_rock_button,
                        self.edit_rock_button,
                        self.pack_rock_init_charm_button,
                        self.edit_charm_button,  # NEW
                        self.pack_charm_bundle_button,  # NEW
                        self.save_bundle_button,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                    wrap=True,
                ),
                self.log_container,
            ],
            spacing=15,
        )

        # Call parent constructor
        super().__init__(
            title="5. Generate Files",
            step_number=5,
            app_state=app_state,
            content_control=content_control,
        )

    # --- Event Handlers and Logic ---
    def on_save_dialog_result(self, e: ft.FilePickerResultEvent):
        zip_path = self._generated_zip_path
        if not e.path:
            self.update_status("Save cancelled.")
            self.save_bundle_button.disabled = False  # Re-enable
            self.page.update()
            return
        try:
            if zip_path and Path(zip_path).exists():
                shutil.move(zip_path, e.path)
                self.update_status("Bundle saved successfully!")
                self._generated_zip_path = None
                self.init_rock_button.disabled = False  # Re-enable first button
                self.page.update()
            else:
                self.update_status("Error: Bundle file not found for saving.")
                self.save_bundle_button.disabled = False
                self.page.update()
        except Exception as ex:
            self.update_status(f"Error saving file: {ex}")
            self.save_bundle_button.disabled = False
            self.page.update()
        finally:
            if self._zip_cleanup_func:
                self._zip_cleanup_func()
                self._zip_cleanup_func = None

    def update_status(self, message, is_log=False):
        current_value = self.log_view.value if self.log_view.value else ""
        if is_log:
            new_line = f"`{message}`\n\n"
        else:
            new_line = f"**{message}**\n\n"
            if not message.startswith("ERROR"):
                self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                self.page.snack_bar.open = True

        self.log_view.value = current_value + new_line
        self.log_scroll_column.scroll_to(
            offset=-1, duration=100, curve=ft.AnimationCurve.EASE_OUT
        )
        self.log_view.update()
        self.page.update()

    # --- Rock Init ---
    def run_initialization_in_thread(self):
        job_id = None
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")
            project_name = data.get("sourceProjectName")
            project_path = JOB_STORE.get(job_id)
            if not project_path:
                raise ValueError("Job not found or expired.")
            rock_gen = RockcraftGenerator(
                project_path, project_name, data.get("framework", "")
            )
            logging.info("Starting Rock initialization.")
            self._rockcraft_yaml_path = rock_gen.init_rockcraft(
                status_callback=self.update_status
            )
            self.edit_rock_button.disabled = False
            self.edit_rock_button.visible = True
            self.pack_rock_init_charm_button.disabled = False  # Next step
            self.pack_rock_init_charm_button.visible = True
            self.update_status("Rockcraft initialized.")
        except Exception as e:
            self.update_status(f"**ERROR:** {e}", is_log=False)
            print(f"Initialization error: {e}")
            self.init_rock_button.disabled = False  # Re-enable on error
        finally:
            self.page.update()

    def on_init_rock(self, e):
        self.log_container.visible = True
        self.log_view.value = "**Starting Rock initialization...**\n\n"
        self.init_rock_button.disabled = True
        self.edit_rock_button.visible = False
        self.edit_rock_button.disabled = True
        self.pack_rock_init_charm_button.visible = False
        self.pack_rock_init_charm_button.disabled = True
        self.edit_charm_button.visible = False
        self.edit_charm_button.disabled = True
        self.pack_charm_bundle_button.visible = False
        self.pack_charm_bundle_button.disabled = True
        self.save_bundle_button.visible = False
        self.save_bundle_button.disabled = True
        self._rockcraft_yaml_path = None
        self._rock_file_path = None
        self._charmcraft_yaml_path = None
        self._charm_file_path = None
        self._generated_zip_path = None
        if self._zip_cleanup_func:
            self._zip_cleanup_func()
            self._zip_cleanup_func = None
        if self._charm_cleanup_func:
            self._charm_cleanup_func()
            self._charm_cleanup_func = None
        self.page.update()
        thread = threading.Thread(target=self.run_initialization_in_thread, daemon=True)
        thread.start()

    # --- Rock Edit ---
    def on_edit_rockcraft(self, e):
        if (
            not self._rockcraft_yaml_path
            or not Path(self._rockcraft_yaml_path).exists()
        ):
            self.update_status("Error: rockcraft.yaml path not found.")
            return
        try:
            with open(self._rockcraft_yaml_path, "r") as f:
                self.rock_yaml_editor.value = f.read()
            self.rock_edit_modal.open = True
            self.page.update()
        except Exception as ex:
            self.update_status(f"Error reading rockcraft.yaml: {ex}")

    def on_save_rock_yaml(self, e):
        if self._rockcraft_yaml_path:
            try:
                with open(self._rockcraft_yaml_path, "w") as f:
                    f.write(self.rock_yaml_editor.value)
                self.update_status("rockcraft.yaml saved.")
            except Exception as ex:
                self.update_status(f"Error saving rockcraft.yaml: {ex}")
        self.rock_edit_modal.open = False
        self.page.update()

    def on_cancel_rock_yaml(self, e):
        self.rock_edit_modal.open = False
        self.page.update()

    # --- Pack Rock & Init Charm ---
    def run_pack_rock_init_charm_thread(self):
        job_id = None
        charm_gen = None  # Define charm_gen here for cleanup
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")
            project_path = JOB_STORE.get(job_id)
            if not project_path:
                raise ValueError("Job not found or expired.")

            logging.info("Starting Rock packing.")
            # Pack Rock
            rock_gen = RockcraftGenerator(project_path, data.get("framework", ""))
            self._rock_file_path = rock_gen.pack_rockcraft(
                status_callback=self.update_status
            )

            # Init Charm
            config_options_dicts = [
                opt.to_dict() for opt in data.get("configOptions", [])
            ]
            integration_ids = [
                integ.get("id") for integ in data.get("integrations", [])
            ]
            charm_gen = CharmcraftGenerator(
                integration_ids,
                config_options_dicts,
                data.get("sourceProjectName", "my-charm"),
            )
            # Store cleanup func BEFORE potential errors in init
            self._charm_cleanup_func = charm_gen.cleanup
            self._charmcraft_yaml_path = charm_gen.init_charmcraft(
                status_callback=self.update_status
            )

            # Enable next steps
            self.edit_charm_button.disabled = False
            self.edit_charm_button.visible = True
            self.pack_charm_bundle_button.disabled = False
            self.pack_charm_bundle_button.visible = True
            self.update_status("Rock packed & Charm initialized.")

        except Exception as e:
            self.update_status(f"**ERROR:** {e}", is_log=False)
            print(f"Pack Rock/Init Charm error: {e}")
            self.pack_rock_init_charm_button.disabled = False  # Re-enable on error
            if self._charm_cleanup_func:
                self._charm_cleanup_func()
                self._charm_cleanup_func = None  # Cleanup charm temp dir on error
        finally:
            self.page.update()

    def on_pack_rock_init_charm(self, e):
        self.pack_rock_init_charm_button.disabled = True
        self.edit_rock_button.disabled = True  # Disable previous edit
        self.edit_charm_button.visible = False
        self.edit_charm_button.disabled = True
        self.pack_charm_bundle_button.visible = False
        self.pack_charm_bundle_button.disabled = True
        self.page.update()
        thread = threading.Thread(
            target=self.run_pack_rock_init_charm_thread, daemon=True
        )
        thread.start()

    # --- Charm Edit --- (NEW)
    def on_edit_charmcraft(self, e):
        if (
            not self._charmcraft_yaml_path
            or not Path(self._charmcraft_yaml_path).exists()
        ):
            self.update_status("Error: charmcraft.yaml path not found.")
            return
        try:
            with open(self._charmcraft_yaml_path, "r") as f:
                self.charm_yaml_editor.value = f.read()
            self.charm_edit_modal.open = True
            self.page.update()
        except Exception as ex:
            self.update_status(f"Error reading charmcraft.yaml: {ex}")

    def on_save_charm_yaml(self, e):
        if self._charmcraft_yaml_path:
            try:
                # Note: We don't need to call charm_gen.update_charmcraft_yaml here
                # because we are directly writing the user's edits.
                # If we wanted programmatic updates *plus* user edits,
                # we'd need a more complex merge strategy.
                with open(self._charmcraft_yaml_path, "w") as f:
                    f.write(self.charm_yaml_editor.value)
                self.update_status("charmcraft.yaml saved.")
            except Exception as ex:
                self.update_status(f"Error saving charmcraft.yaml: {ex}")
        self.charm_edit_modal.open = False
        self.page.update()

    def on_cancel_charm_yaml(self, e):
        self.charm_edit_modal.open = False
        self.page.update()

    # --- Pack Charm & Bundle --- (NEW)
    def run_charm_packing_and_bundling_in_thread(self):
        job_id = None
        zip_cleanup = None  # Define zip_cleanup here
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")
            # We need the charm instance created in the previous step to pack
            # This requires restructuring how charm_gen is stored or passed,
            # For simplicity, we create a new one pointing to the existing dir
            if not self._charm_cleanup_func:  # Check if init was successful
                raise RuntimeError("Charmcraft instance not properly initialized.")

            # Recreate generator to use pack method - needs access to temp dir path etc.
            # A better approach might be to store the charm_gen instance itself.
            config_options_dicts = [
                opt.to_dict() for opt in data.get("configOptions", [])
            ]
            integration_ids = [
                integ.get("id") for integ in data.get("integrations", [])
            ]
            # We need the temp_dir path which was created by the original charm_gen
            # This is fragile. Refactoring CharmcraftGenerator to separate init/pack better is advised.
            # Assuming CharmcraftGenerator stores temp_dir path correctly.
            # We need to find the CharmcraftGenerator instance or its path.
            # Let's assume self._charm_cleanup_func gives access or we store temp path.
            # HACK: Re-create CharmcraftGenerator, assuming its constructor is idempotent with existing dir
            # This relies on the internal implementation detail that the temp dir path is deterministic or stored
            # A cleaner way: Store self.charm_gen instance variable.
            charm_gen_packer = CharmcraftGenerator(
                integration_ids,
                config_options_dicts,
                data.get("sourceProjectName", "my-charm"),
            )
            # Crucially, point it to the *existing* temp dir created during init
            charm_gen_packer.temp_dir = (
                self._charm_cleanup_func.__self__.temp_dir_obj.name
            )  # Access via stored cleanup
            charm_gen_packer.charm_project_path = os.path.join(
                charm_gen_packer.temp_dir, charm_gen_packer.project_name
            )

            # Update YAML *before* packing if it wasn't edited manually
            # We should only call update if the user didn't save manually
            # Add state to track if manual save happened? For now, always update before pack.
            if self._charmcraft_yaml_path:
                charm_gen_packer.update_charmcraft_yaml(
                    self._charmcraft_yaml_path, status_callback=self.update_status
                )

            self._charm_file_path = charm_gen_packer.pack_charmcraft(
                status_callback=self.update_status
            )

            # --- Bundle ---
            if not self._rock_file_path:
                raise RuntimeError("Rock file path not found.")
            self.update_status("Bundling artifacts...")
            zip_path, zip_cleanup = BundleArtifacts(
                self._rock_file_path, self._charm_file_path
            )

            self._generated_zip_path = zip_path
            self._zip_cleanup_func = zip_cleanup
            self.save_bundle_button.disabled = False
            self.save_bundle_button.visible = True
            self.update_status("Bundle created. Click 'Save Bundle' to download.")

        except Exception as e:
            error_message = f"**ERROR:** {e}"
            self.update_status(error_message, is_log=False)
            print(f"Charm Packing/Bundling error: {e}")
            self.pack_charm_bundle_button.disabled = False  # Re-enable on error
        finally:
            # Clean up job directory ONLY NOW
            if job_id and job_id in JOB_STORE:
                shutil.rmtree(TEMP_STORAGE_PATH / job_id, ignore_errors=True)
                del JOB_STORE[job_id]
            # Charm cleanup happens when CharmcraftGenerator instance goes out of scope or via self._charm_cleanup_func
            # We might call self._charm_cleanup_func() here if needed, depends on logic flow.
            # For now, it's handled when the CharmcraftGenerator object is destroyed.
            self.page.update()

    def on_pack_charm_and_bundle(self, e):
        self.pack_charm_bundle_button.disabled = True
        self.edit_charm_button.disabled = True  # Disable previous edit
        self.save_bundle_button.visible = False  # Hide save until ready
        self.page.update()
        thread = threading.Thread(
            target=self.run_charm_packing_and_bundling_in_thread, daemon=True
        )
        thread.start()

    # --- Save Bundle ---
    def on_save_bundle(self, e):
        if self._generated_zip_path:
            self.save_picker.data = self._generated_zip_path
            self.save_picker.save_file(
                dialog_title="Save Your Bundle", file_name="rock-and-charm-bundle.zip"
            )
            self.save_bundle_button.disabled = True
            self.page.update()
        else:
            self.update_status("Error: No bundle file available to save.")
