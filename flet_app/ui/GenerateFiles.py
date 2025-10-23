import flet as ft
from .AccordionStep import AccordionStep # Corrected import path
import shutil
import threading
import time
from pathlib import Path
import os # Import os

# Import logic modules
from logic.rockcraft import RockcraftGenerator
from logic.charmcraft import CharmcraftGenerator
from logic.bundler import BundleArtifacts

# Import state
from state import TEMP_STORAGE_PATH, JOB_STORE

class GenerateFiles(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]
        
        # --- State specific to this step ---
        self._generated_zip_path = None
        self._zip_cleanup_func = None

        # --- UI Controls ---
        self.log_view = ft.Markdown(
            "", 
            selectable=True,
            #   expand=True,
            extension_set=ft.MarkdownExtensionSet.COMMON_MARK,
            auto_follow_links=False,
        )
        self.log_scroll_column = ft.Column(
            [self.log_view], 
            scroll=ft.ScrollMode.ALWAYS, 
            # expand=True
        )
        
        self.log_container = ft.Container(
            content=self.log_scroll_column, # Use the scrollable column
            border=ft.border.all(1, ft.Colors.BLACK26),
            border_radius=5, 
            padding=10, 
            height=300,
            visible=False, 
            bgcolor=ft.Colors.WHITE, 
            # REMOVED expand=True - Let width be determined by parent Column
            # Horizontal expansion is implicitly handled by being in a Column
        )
        self.save_picker = ft.FilePicker(on_result=self.on_save_dialog_result) # Use bound method
        self.page.overlay.append(self.save_picker)

        self.generate_button = ft.ElevatedButton(
            "Generate Bundle", # Changed text
            on_click=self.on_generate,
            icon=ft.Icons.PLAY_ARROW_ROUNDED # Changed icon
        )
        
        self.save_button = ft.ElevatedButton(
            "Save Bundle",
            on_click=self.on_save_bundle,
            icon=ft.Icons.SAVE,
            disabled=True, # Start disabled
        )
        
        content_control = ft.Column([
            ft.Text("All steps complete. You can now generate your files.", size=16),
            ft.Row(
                [self.generate_button, self.save_button],
                alignment=ft.MainAxisAlignment.START,
                spacing=10
            ),
            self.log_container,
        ], spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        # Call parent constructor
        super().__init__(
            title="5. Generate Files",
            step_number=5,
            app_state=app_state,
            content_control=content_control,
        )

    # --- Event Handlers and Logic ---
    def on_save_dialog_result(self, e: ft.FilePickerResultEvent):
        zip_path = self._generated_zip_path # Use the stored path
        
        if not e.path: # User cancelled
            self.update_status("Save cancelled.")
            # Don't clean up zip yet, user might click save again
            return
        try:
            if zip_path and Path(zip_path).exists():
                shutil.move(zip_path, e.path)
                self.update_status("Bundle saved successfully!")
                self._generated_zip_path = None # Clear path after successful save
            else:
                 self.update_status("Error: Bundle file not found for saving.")
        except Exception as ex:
            self.update_status(f"Error saving file: {ex}")
        finally:
            # Clean up the zip file only AFTER save attempt (success, fail, or cancel)
            if self._zip_cleanup_func:
                self._zip_cleanup_func()
                self._zip_cleanup_func = None # Prevent multiple cleanups


    def update_status(self, message, is_log=False):
        """Helper to send status updates to the UI thread."""
        current_value = self.log_view.value if self.log_view.value else ""
        
        if is_log:
            new_line = f"`{message}`\n\n"
        else:
            new_line = f"**{message}**\n\n"
            if not message.startswith("ERROR"): # Don't show errors in snackbar too
                self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                self.page.snack_bar.open = True
            
        self.log_view.value = current_value + new_line
        
        self.log_scroll_column.scroll_to(offset=-1, duration=100, curve=ft.AnimationCurve.EASE_OUT)

        self.log_view.update() # Necessary for Markdown updates
        self.page.update() # Update the page to show scroll/snackbar

    def run_generation_in_thread(self):
        """The core logic that runs in the background."""
        charm_cleanup = None # Define cleanup functions outside try
        zip_cleanup = None
        job_id = None
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")
            project_path = JOB_STORE.get(job_id)
            
            if not project_path: raise ValueError("Job not found or expired.")

            rock_gen = RockcraftGenerator(project_path, data.get("framework", ""), data.get("sourceProjectName", "my_rock"))
            rock_file_path = rock_gen.generate(status_callback=self.update_status)

            config_options_dicts = [opt.to_dict() for opt in data.get("configOptions", [])]
            integration_ids = [integ.get('id') for integ in data.get("integrations", [])]

            charm_gen = CharmcraftGenerator(
                integration_ids, config_options_dicts, data.get("sourceProjectName", "my-charm")
            )
            charm_file_path, charm_cleanup = charm_gen.generate(status_callback=self.update_status)
            
            self.update_status("Bundling artifacts...")
            zip_path, zip_cleanup = BundleArtifacts(rock_file_path, charm_file_path)

            # Store the path and cleanup for the save button, don't trigger save yet
            self._generated_zip_path = zip_path
            self._zip_cleanup_func = zip_cleanup # Store cleanup function
            self.save_button.disabled = False
            self.update_status("Bundle created. Click 'Save Bundle' to download.")
            
        except Exception as e:
            error_message = f"**ERROR:** {e}"
            self.update_status(error_message, is_log=False)
            print(f"Generation error: {e}")
        finally:
            # Clean up job directory and charm temp dir regardless of success/failure
            if job_id and job_id in JOB_STORE:
                shutil.rmtree(TEMP_STORAGE_PATH / job_id, ignore_errors=True)
                del JOB_STORE[job_id]
            if charm_cleanup:
                charm_cleanup()
                
            # Re-enable generate button ONLY if there was an error
            if self.log_view.value and "**ERROR:**" in self.log_view.value:
                 self.generate_button.disabled = False
            
            self.page.update()

    def on_generate(self, e):
        """Starts the background generation thread."""
        self.log_container.visible = True
        self.log_view.value = "**Starting generation...**\n\n" # Initial message
        self.generate_button.disabled = True
        self.save_button.disabled = True # Disable save button during generation
        self.page.update()
        
        # Clean up any leftover zip from a previous failed/cancelled save
        if self._zip_cleanup_func:
            self._zip_cleanup_func()
            self._zip_cleanup_func = None
        self._generated_zip_path = None

        thread = threading.Thread(target=self.run_generation_in_thread, daemon=True)
        thread.start()

    # --- Handler for the save button ---
    def on_save_bundle(self, e):
        """Triggers the file save dialog using the generated zip path."""
        if self._generated_zip_path:
            # Store the zip path on the picker *before* calling save_file
            self.save_picker.data = self._generated_zip_path 
            self.save_picker.save_file(
                dialog_title="Save Your Bundle",
                file_name="rock-and-charm-bundle.zip"
            )
            # Disable save button after clicking to prevent multiple saves of same file
            self.save_button.disabled = True 
            self.page.update()
        else:
            self.update_status("Error: No bundle file available to save.")

