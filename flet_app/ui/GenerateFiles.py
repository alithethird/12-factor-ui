
# Import logic modules
# Import state
import shutil
import subprocess
import threading
from pathlib import Path

import flet as ft
from logic.bundler import BundleArtifacts
from logic.charmcraft import CharmcraftGenerator
from logic.rockcraft import RockcraftGenerator
from state import JOB_STORE

from .AccordionStep import AccordionStep


class GenerateFiles(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]

        # --- State specific to this step ---
        self._generated_zip_path = None
        self._rockcraft_yaml_path = None
        self._rock_file_path = None
        self._rock_pack_complete = False
        self._charmcraft_yaml_path = None
        self._charm_file_path = None
        self._charm_pack_complete = False
        self._charm_temp_dir_path = None

        # --- UI Controls ---
        self.log_view = ft.Markdown(
            "",
            selectable=True,
            expand=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
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
            bgcolor=ft.Colors.WHITE,
            expand=True,
            visible=False,
        )
        
        self.save_picker = ft.FilePicker(on_result=self.on_save_dialog_result)
        self.page.overlay.append(self.save_picker)

        self.init_rock_button = ft.ElevatedButton(
            "Init Rock", on_click=self.on_init_rock, icon=ft.Icons.PLAY_ARROW_ROUNDED
        )
        self.init_charm_button = (
            ft.ElevatedButton(
                "Init Charm",
                on_click=self.on_init_charm,
                icon=ft.Icons.PLAY_ARROW_ROUNDED,  # Changed icon
                disabled=False,  # Initially enabled
            )
        )
        self.edit_rock_button = ft.ElevatedButton(
            "Edit Rock (Opt.)",
            on_click=self.on_edit_rockcraft,
            icon=ft.Icons.EDIT,
            disabled=True,
        )
        self.pack_rock_button = ft.ElevatedButton(
            "Pack Rock",
            on_click=self.on_pack_rock,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=True,
        )
        self.edit_charm_button = ft.ElevatedButton(
            "Edit Charm (Opt.)",
            on_click=self.on_edit_charmcraft,
            icon=ft.Icons.EDIT,
            disabled=True,
        )
        self.pack_charm_button = ft.ElevatedButton(
            "Pack Charm",
            on_click=self.on_pack_charm,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=True,
        )
        self.save_bundle_button = ft.ElevatedButton(
            "Save Bundle",
            on_click=self.on_save_bundle,
            icon=ft.Icons.SAVE,
            disabled=True,
        )

        # --- Modals ---
        self.rock_yaml_editor = ft.TextField(multiline=True, expand=True, min_lines=15)
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

        self.charm_yaml_editor = ft.TextField(multiline=True, expand=True, min_lines=15)
        self.charm_edit_modal = ft.AlertDialog(
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
                    "Initialize Rock and/or Charm, then proceed with packing/bundling.",
                    size=16,
                ),
                ft.Row(
                    [
                        self.init_rock_button,
                        self.edit_rock_button,
                        self.pack_rock_button,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                    wrap=True,
                ),
                ft.Row(
                    [
                        self.init_charm_button, 
                        self.edit_charm_button,
                        self.pack_charm_button,
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
            title="5. Generate Files",  # Adjust step number if needed
            step_number=5,  # Adjust step number if needed
            app_state=app_state,
            content_control=content_control,
        )

    # --- Helper Methods ---
    def _check_both_packs_complete(self):
        """Check if both rock and charm packs are complete and enable save bundle button if so."""
        if self._rock_pack_complete and self._charm_pack_complete:
            self.save_bundle_button.disabled = False
            self.page.update()
            return True
        return False

    # --- Event Handlers and Logic ---
    def on_save_dialog_result(self, e: ft.FilePickerResultEvent):
        zip_path = self._generated_zip_path
        if not e.path:
            self.update_status("Save cancelled.")
            self.save_bundle_button.disabled = False
            self.page.update()
            return
        try:
            if zip_path and Path(zip_path).exists():
                shutil.move(zip_path, e.path)
                self.update_status("Bundle saved successfully!")
                self._generated_zip_path = None
                # Re-enable initial buttons after successful save
                self.init_rock_button.disabled = False
                self.init_charm_button.disabled = False
                self.page.update()
            else:
                self.update_status("Error: Bundle file not found for saving.")
                self.save_bundle_button.disabled = False
                self.page.update()
        except Exception as ex:
            self.update_status(f"Error saving file: {ex}")
            self.save_bundle_button.disabled = False
            self.page.update()

    def update_status(self, message, is_log=False):
        if is_log:
            new_line = f"`{message}`\n\n"
        else:
            new_line = f"**{message}**\n\n"
            if not message.startswith("ERROR"):
                self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=3000)
                self.page.snack_bar.open = True

        self.log_view.value += new_line
        self.log_scroll_column.scroll_to(
            offset=-1, duration=100, curve=ft.AnimationCurve.EASE_OUT
        )
        self.log_view.update()
        self.page.update()

    # --- Rock Init ---
    def rock_init(self):
        try:
            data = self.app_state["get_form_data"]()
            project_path = JOB_STORE.get(data.get("jobId"))
            if not project_path:
                raise ValueError("Job not found or expired.")
            rock_gen = RockcraftGenerator(
                project_path, data.get("sourceProjectName"), data.get("framework", "")
            )
            self._rockcraft_yaml_path = rock_gen.init_rockcraft(
                status_callback=self.update_status
            )
            # Enable rock-specific next steps
            self.edit_rock_button.disabled = False
            self.pack_rock_button.disabled = False
            # Re-enable charm init button
            self.init_charm_button.disabled = False

        except Exception as e:
            self.update_status(f"**ERROR:** {e}", is_log=False)
            print(f"Initialization error: {e}")
            # Re-enable both init buttons on error
            self.init_rock_button.disabled = False
            self.init_charm_button.disabled = False
        finally:
            self.page.update()

    def rock_pack(self, framework, project_path, project_name):
        """
        Process target function for packing the rock.
        Wraps the pack operation with better error detection.
        """

        if not project_path:
            raise ValueError("Job not found or expired.")

        try:
            rock_gen = RockcraftGenerator(project_path, project_name, framework)
            self._rock_file_path = rock_gen.pack_rockcraft(status_callback=self.update_status)
            
            # Mark rock pack as complete
            self._rock_pack_complete = True
            self._check_both_packs_complete()
            
        except subprocess.TimeoutExpired as te:
            self.update_status(
                f"**ERROR:** Rock packing operation timed out after {te.timeout} seconds. "
                "The project is likely too large or your system doesn't have enough resources. "
                "Try reducing dependencies or running on a machine with more RAM/CPU."
            )
            self._rock_pack_complete = False
            raise
        except Exception as e:
            error_msg = str(e)
            if "killed" in error_msg.lower() or "signal" in error_msg.lower():
                self.update_status(
                    "**ERROR:** Rock packing was terminated by the system. "
                    "This usually means the system ran out of memory. "
                    "Close other applications and try again with a simpler project."
                )
            else:
                self.update_status(f"**ERROR:** Rock packing failed: {e}")
            self._rock_pack_complete = False
            raise
    def on_init_rock(self, e):
        self.log_container.visible = True
        self.log_view.value += "**Starting Rock initialization...**\n\n"
        self.init_rock_button.disabled = True
        self.edit_rock_button.disabled = True
        self.pack_rock_button.disabled = True

        # Hide final steps
        self.save_bundle_button.disabled = True

        # Clear only rock-related state
        self._rockcraft_yaml_path = None
        self._rock_file_path = None
        self._rock_pack_complete = False

        # Clear bundle state
        self._generated_zip_path = None

        self.page.update()
        thread = threading.Thread(target=self.rock_init, daemon=True)
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

    # --- Pack Rock ---
    def on_pack_rock(self, e):
        # Disable buttons that interfere or depend on this
        self.pack_rock_button.disabled = True
        self.edit_rock_button.disabled = True
        self.init_rock_button.disabled = True  # Prevent re-init during pack
        # self.init_charm_button.disabled = True  # Prevent charm init during rock pack
        self.pack_charm_button.disabled = (
            True  # Cannot bundle until rock is packed
        )

        self.page.update()

        def _run_rock_packer_in_thread():
            try:
                data = self.app_state["get_form_data"]()
                job_id = data.get("jobId")
                project_path = JOB_STORE.get(job_id)
                project_name = data.get("sourceProjectName", "my-rock")
                if not project_path:
                    raise ValueError("Job not found or expired.")

                p_rock = threading.Thread(
                    target=self.rock_pack,
                    args=(
                        data.get("framework", ""),
                        project_path,
                        project_name,
                    ),
                )
                p_rock.start()
                p_rock.join()

            except Exception as ex:
                error_msg = str(ex)
                # Provide helpful error messages for common issues
                if "timed out" in error_msg.lower():
                    self.update_status(
                        f"**ERROR:** Rock packing timed out. The project may be too large or your system may not have enough resources. Try reducing project complexity or closing other applications.",
                        is_log=False
                    )
                elif "killed" in error_msg.lower() or "memory" in error_msg.lower():
                    self.update_status(
                        f"**ERROR:** Rock packing was terminated due to insufficient system resources. Close other applications and try again.",
                        is_log=False
                    )
                else:
                    self.update_status(f"**ERROR:** {ex}", is_log=False)
                
                # Re-enable buttons on error
                self.pack_rock_button.disabled = False
                self.edit_rock_button.disabled = False
                self.init_rock_button.disabled = False
                self.init_charm_button.disabled = False
                # Keep bundle disabled if error occurred here
                self.pack_charm_button.disabled = True
                self._rock_pack_complete = False
            finally:
                if not hasattr(self, '_rock_pack_complete') or not self._rock_pack_complete:
                    # Only show success message if rock pack actually completed
                    pass
                else:
                    self.update_status("Rock packed successfully.")
                # Re-enable relevant buttons
                self.edit_rock_button.disabled = False
                self.init_rock_button.disabled = False  # Can re-init now
                self.init_charm_button.disabled = (
                    False  # Can init charm now
                )
                self.page.update()

        thread = threading.Thread(target=_run_rock_packer_in_thread, daemon=True)
        thread.start()

    # --- Init Charm ---
    def on_init_charm(self, e):
        self.log_container.visible = True
        self.log_view.value += "**Starting Charm initialization...**\n\n"  # Add message
        # Disable both init buttons during the process
        self.init_charm_button.disabled = True
        self.init_rock_button.disabled = True
        # Hide subsequent charm steps
        self.edit_charm_button.disabled = True
        self.pack_charm_button.disabled = True
        # Don't hide rock steps
        # Hide final step
        self.save_bundle_button.disabled = True

        # Clear only charm-related state
        self._charmcraft_yaml_path = None
        self._charm_file_path = None
        self._charm_pack_complete = False
        if self._charm_temp_dir_path:  # Clean up previous charm temp dir IF IT EXISTS
            shutil.rmtree(self._charm_temp_dir_path, ignore_errors=True)
            self._charm_temp_dir_path = None
        # Don't clear rock state

        # Clear bundle state
        self._generated_zip_path = None

        self.page.update()

        def _run_charm_init_in_thread():
            try:
                data = self.app_state["get_form_data"]()
                job_id = data.get("jobId")  # Still useful for context maybe

                config_options_dicts = [
                    opt.to_dict() for opt in data.get("configOptions", [])
                ]
                integration_ids = [
                    integ.get("id") for integ in data.get("integrations", [])
                ]
                # Try getting project name from source, default otherwise
                project_name = data.get("sourceProjectName")
                if not project_name:
                    # Attempt to get from job store path if sourceProjectName wasn't set (e.g., direct upload with odd name)
                    job_path = JOB_STORE.get(job_id)
                    if job_path:
                        project_name = Path(job_path).name
                    else:
                        project_name = "my-charm"  # Final fallback
                project_name = project_name.replace("_", "-").lower().replace(" ", "-")
                project_path = JOB_STORE.get(job_id)

                p_charm = threading.Thread(
                    target=self.charm_init,
                    args=(
                        config_options_dicts,
                        integration_ids,
                        project_path,
                        project_name,
                    ),
                )
                p_charm.start()
                p_charm.join()
            except Exception as ex:
                self.update_status(f"**ERROR:** {ex}", is_log=False)
                # Re-enable both init buttons on error
                self.init_charm_button.disabled = False
                self.init_rock_button.disabled = False
            finally:
                self._charmcraft_yaml_path = project_path + "/charm/charmcraft.yaml"
                self.edit_charm_button.disabled = False
                self.pack_charm_button.disabled = False
                self.page.update()

        thread = threading.Thread(target=_run_charm_init_in_thread, daemon=True)
        thread.start()

    # --- Charm Edit ---
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

    def charm_init(
        self, config_options_dicts, integration_ids, project_path, project_name
    ):
        """
        Process target function for initializing the charm.
        Sends logs, the new temp_dir path, and results back through the queue.
        """
        try:

            # Assuming CharmcraftGenerator handles its temp dir correctly now
            charm_gen = CharmcraftGenerator(
                integration_ids,
                config_options_dicts,
                project_path,
                project_name,
            )
            yaml_path, temp_dir = charm_gen.init_charmcraft(status_callback=self.update_status)
        
            # Update YAML if it exists (it should after init)
            if yaml_path:
                charm_gen.update_charmcraft_yaml(
                    yaml_path, status_callback=self.update_status
                )
        except Exception as e:
            self.update_status(f"ERROR: {str(e)}")

    def charm_pack(self):
        job_id = None
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")  # Keep for potential cleanup logic
            self._charm_temp_dir_path = JOB_STORE.get(job_id)
            # --- Pre-checks ---
            if (
                not self._charm_temp_dir_path
                or not Path(self._charm_temp_dir_path).exists()
            ):
                raise RuntimeError(
                    "Charm project directory not found. Please initialize charm first."
                )
            # --- End Pre-checks ---

            config_options_dicts = [
                opt.to_dict() for opt in data.get("configOptions", [])
            ]
            integration_ids = [
                integ.get("id") for integ in data.get("integrations", [])
            ]
            project_name = data.get("sourceProjectName", "my-charm")
            project_name = project_name.replace("_", "-").lower().replace(" ", "-")

            # Recreate generator instance using the existing temp path
            charm_gen_packer = CharmcraftGenerator(
                integration_ids,
                config_options_dicts,
                project_path=self._charm_temp_dir_path,  # Pass the existing path
                project_name=project_name,
            )


            # Pack the charm
            self._charm_file_path = charm_gen_packer.pack_charmcraft(
                status_callback=self.update_status
            )
            
            # Mark charm pack as complete and check if both are done
            self._charm_pack_complete = True
            self._check_both_packs_complete()

        except Exception as e:
            error_message = f"**ERROR:** {e}"
            self.update_status(error_message, is_log=False)
            print(f"Charm Packing error: {e}")
            # Re-enable relevant buttons on error
            self.edit_charm_button.disabled = False  # Re-enable editing
            # Also re-enable init buttons if things went wrong
            self.init_rock_button.disabled = False
            self.init_charm_button.disabled = False
        finally:
            self.page.update()

    def on_pack_charm(self, e):
        # Disable buttons that interfere
        self.pack_charm_button.disabled = True
        self.edit_charm_button.disabled = True
        self.init_charm_button.disabled = True  # Prevent re-init during pack
        self.init_rock_button.disabled = True  # Prevent rock changes during pack
        self.pack_rock_button.disabled = (
            True  # Prevent rock packing during charm pack
        )

        self.save_bundle_button.disabled = True
        self.page.update()
        thread = threading.Thread(
            target=self.charm_pack, daemon=True
        )
        thread.start()

    # --- Save Bundle ---
    def on_save_bundle(self, e):
        thread = threading.Thread(
            target=self.run_bundling_in_thread, daemon=True
        )
        thread.start()
        thread.join()
        if self._generated_zip_path:
            self.save_picker.data = self._generated_zip_path
            project_name = self.app_state["form_data"].get(
                "sourceProjectName", "bundle"
            )
            save_filename = f"{project_name}-rock-charm.zip"
            self.save_picker.save_file(
                dialog_title="Save Your Bundle", file_name=save_filename
            )
            self.save_bundle_button.disabled = True
            self.page.update()
        else:
            self.update_status("Error: No bundle file available to save.")

    # --- Pack Charm & Bundle ---
    def run_bundling_in_thread(self):
        job_id = None
        zip_cleanup = None
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")  # Keep for potential cleanup logic
            self._charm_temp_dir_path = JOB_STORE.get(job_id)
            # --- Pre-checks ---
            if not self._charm_file_path or not Path(self._charm_file_path).exists():
                raise RuntimeError(
                    "Packed charm file not found. Please pack the charm first."
                )
            if not self._rock_file_path or not Path(self._rock_file_path).exists():
                raise RuntimeError(
                    "Packed rock file not found. Please pack the rock first."
                )
            # --- End Pre-checks ---

            # --- Bundle ---
            self.update_status("Bundling artifacts...")
            zip_path = BundleArtifacts(
                self._rock_file_path, self._charm_file_path
            )

            self._generated_zip_path = zip_path
            self.save_bundle_button.disabled = False
            self.update_status("Bundle created.")
            # Re-enable init buttons after successful bundle
            self.init_rock_button.disabled = False
            self.init_charm_button.disabled = False

        except Exception as e:
            error_message = f"**ERROR:** {e}"
            self.update_status(error_message, is_log=False)
            print(f"Charm Bundling error: {e}")
            # Re-enable relevant buttons on error
            self.pack_charm_button.disabled = False  # Re-enable itself
            self.edit_charm_button.disabled = False  # Re-enable editing
            # Also re-enable init buttons if things went wrong
            self.init_rock_button.disabled = False
            self.init_charm_button.disabled = False

        finally:
            # Clean up job directory (rock source) - only if bundling succeeded or failed here
            # Maybe keep it if only charm packing failed? Decision needed.
            # For now, let's assume we clean up rock source if we reached this point.
            if job_id and job_id in JOB_STORE:
                job_path_to_clean = JOB_STORE.pop(
                    job_id
                )  # Get path and remove from store
                shutil.rmtree(job_path_to_clean, ignore_errors=True)
                self.update_status(
                    f"Cleaned up app source: {job_path_to_clean}", is_log=True
                )

            self.page.update()
