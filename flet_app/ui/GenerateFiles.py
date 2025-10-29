import flet as ft
from .AccordionStep import AccordionStep
import shutil
import threading
import time
from pathlib import Path
import os
import queue  # Import the standard queue for Empty exception
from multiprocessing import Process, Queue  # Import Process and Queue

# Import logic modules
from logic.rockcraft import RockcraftGenerator
from logic.charmcraft import CharmcraftGenerator
from logic.bundler import BundleArtifacts

# Import state
from state import TEMP_STORAGE_PATH, JOB_STORE


# --- NEW: Top-level function for Rock packing Process ---
# This MUST be a top-level function so it can be "pickled"
# by multiprocessing.
def _rock_packer_process(log_queue, job_id, framework, project_path):
    """
    Process target function for packing the rock.
    Sends logs and results back through the queue.
    """
    try:
        # This proxy callback runs in the child process
        def status_callback(message, is_log=True):
            log_queue.put(("LOG", (message, is_log)))

        if not project_path:
            raise ValueError("Job not found or expired.")

        project_name = "test-rock"
        print(f"{project_name=}")
        rock_gen = RockcraftGenerator(project_path, project_name, framework)
        rock_file_path = rock_gen.pack_rockcraft(status_callback=status_callback)

        # Send the success signal and the result
        log_queue.put(("ROCK_SUCCESS", rock_file_path))
    except Exception as e:
        # Send the error
        log_queue.put(("ERROR", str(e)))
    finally:
        # Ensure the queue is closed from the process side
        log_queue.close()


# --- NEW: Top-level function for Charm init Process ---
def _charm_init_process(
    log_queue, job_id, config_options_dicts, integration_ids, project_name
):
    """
    Process target function for initializing the charm.
    Sends logs, the new temp_dir path, and results back through the queue.
    """
    try:

        def status_callback(message, is_log=True):
            log_queue.put(("LOG", (message, is_log)))

        charm_gen = CharmcraftGenerator(
            integration_ids,
            config_options_dicts,
            project_name,
        )

        # init_charmcraft now returns (yaml_path, temp_dir)
        yaml_path, temp_dir = charm_gen.init_charmcraft(status_callback=status_callback)

        # Send back the data
        log_queue.put(("CHARM_SUCCESS", (yaml_path, temp_dir)))
    except Exception as e:
        log_queue.put(("ERROR", str(e)))
    finally:
        # Ensure the queue is closed from the process side
        log_queue.close()


class GenerateFiles(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]

        # --- State specific to this step ---
        self._generated_zip_path = None
        self._zip_cleanup_func = None
        self._rockcraft_yaml_path = None
        self._rock_file_path = None
        self._charmcraft_yaml_path = None
        self._charm_file_path = None
        self._charm_temp_dir_path = None  # To store charm temp dir path

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
        self.init_rock_button = ft.ElevatedButton(
            "1. Init Rock", on_click=self.on_init_rock, icon=ft.Icons.PLAY_ARROW_ROUNDED
        )
        self.edit_rock_button = ft.ElevatedButton(
            "2. Edit Rock (Opt.)",
            on_click=self.on_edit_rockcraft,
            icon=ft.Icons.EDIT,
            disabled=True,
            visible=False,
        )
        self.pack_rock_init_charm_button = ft.ElevatedButton(
            "3. Pack Rock & Init Charm",
            on_click=self.on_pack_rock_init_charm,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=True,
            visible=False,
        )
        self.edit_charm_button = ft.ElevatedButton(
            "4. Edit Charm (Opt.)",
            on_click=self.on_edit_charmcraft,
            icon=ft.Icons.EDIT,
            disabled=True,
            visible=False,
        )
        self.pack_charm_bundle_button = ft.ElevatedButton(
            "5. Pack Charm & Bundle",
            on_click=self.on_pack_charm_and_bundle,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=True,
            visible=False,
        )
        self.save_bundle_button = ft.ElevatedButton(
            "6. Save Bundle",
            on_click=self.on_save_bundle,
            icon=ft.Icons.SAVE,
            disabled=True,
            visible=False,
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
                    "All steps complete. You can now generate your files.", size=16
                ),
                ft.Row(
                    [
                        self.init_rock_button,
                        self.edit_rock_button,
                        self.pack_rock_init_charm_button,
                        self.edit_charm_button,
                        self.pack_charm_bundle_button,
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
                self.init_rock_button.disabled = False
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
            project_path = JOB_STORE.get(job_id)
            if not project_path:
                raise ValueError("Job not found or expired.")
            rock_gen = RockcraftGenerator(
                project_path, data.get("sourceProjectName"), data.get("framework", "")
            )
            self._rockcraft_yaml_path = rock_gen.init_rockcraft(
                status_callback=self.update_status
            )
            self.edit_rock_button.disabled = False
            self.edit_rock_button.visible = True
            self.pack_rock_init_charm_button.disabled = False
            self.pack_rock_init_charm_button.visible = True
            self.update_status("Rockcraft initialized.")
        except Exception as e:
            self.update_status(f"**ERROR:** {e}", is_log=False)
            print(f"Initialization error: {e}")
            self.init_rock_button.disabled = False
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
        # Clean up charm temp dir from a *previous* run
        if self._charm_temp_dir_path:
            shutil.rmtree(self._charm_temp_dir_path, ignore_errors=True)
            self._charm_temp_dir_path = None
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
    def on_pack_rock_init_charm(self, e):
        """
        Runs the pack and init processes sequentially
        in a background thread to keep the UI responsive.
        Reads logs from a multiprocessing.Queue.
        """
        self.pack_rock_init_charm_button.disabled = True
        self.edit_rock_button.disabled = True
        self.edit_charm_button.visible = False
        self.edit_charm_button.disabled = True
        self.pack_charm_bundle_button.visible = False
        self.pack_charm_bundle_button.disabled = True
        self.page.update()

        # This function runs in a new THREAD
        def _sequential_process_runner():
            log_queue = Queue()

            try:
                # --- 1. Get Data ---
                data = self.app_state["get_form_data"]()
                job_id = data.get("jobId")
                project_path = JOB_STORE.get(job_id)
                if not project_path:
                    raise ValueError("Job not found or expired.")

                # --- 2. Run Rock Packer Process ---
                p_rock = Process(
                    target=_rock_packer_process,
                    args=(log_queue, job_id, data.get("framework", ""), project_path),
                )
                p_rock.start()

                rock_success = False
                while p_rock.is_alive() or not log_queue.empty():
                    try:
                        msg_type, payload = log_queue.get(timeout=0.1)
                        if msg_type == "LOG":
                            self.update_status(payload[0], payload[1])
                        elif msg_type == "ROCK_SUCCESS":
                            self._rock_file_path = payload
                            self.update_status("Rock packed.")
                            rock_success = True
                        elif msg_type == "ERROR":
                            raise RuntimeError(f"Rock packing error: {payload}")
                    except queue.Empty:
                        if not p_rock.is_alive():
                            break  # Process finished
                        continue

                p_rock.join()
                if not rock_success and not self._rock_file_path:
                    raise RuntimeError(
                        "Rock packing process failed or did not return success."
                    )

                # --- 3. Run Charm Init Process ---
                config_options_dicts = [
                    opt.to_dict() for opt in data.get("configOptions", [])
                ]
                integration_ids = [
                    integ.get("id") for integ in data.get("integrations", [])
                ]
                project_name = data.get("sourceProjectName", "my-charm")

                p_charm = Process(
                    target=_charm_init_process,
                    args=(
                        log_queue,
                        job_id,
                        config_options_dicts,
                        integration_ids,
                        project_name,
                    ),
                )
                p_charm.start()

                charm_success = False
                while p_charm.is_alive() or not log_queue.empty():
                    try:
                        msg_type, payload = log_queue.get(timeout=0.1)
                        if msg_type == "LOG":
                            self.update_status(payload[0], payload[1])
                        elif msg_type == "CHARM_SUCCESS":
                            self._charmcraft_yaml_path, self._charm_temp_dir_path = (
                                payload
                            )
                            self.update_status("Charm initialized.")
                            # Enable next steps
                            self.edit_charm_button.disabled = False
                            self.edit_charm_button.visible = True
                            self.pack_charm_bundle_button.disabled = False
                            self.pack_charm_bundle_button.visible = True
                            charm_success = True
                        elif msg_type == "ERROR":
                            raise RuntimeError(f"Charm init error: {payload}")
                    except queue.Empty:
                        if not p_charm.is_alive():
                            break  # Process finished
                        continue

                p_charm.join()
                if not charm_success:
                    raise RuntimeError(
                        "Charm init process failed or did not return success."
                    )

                self.update_status("Charm inited!")  # From original code

            except Exception as ex:
                self.update_status(f"**ERROR:** {ex}", is_log=False)
                self.pack_rock_init_charm_button.disabled = False  # Re-enable on error
            finally:
                log_queue.close()
                log_queue.join_thread()  # Wait for queue feeder thread to exit
                self.page.update()

        # Start the thread that manages the processes
        thread = threading.Thread(target=_sequential_process_runner, daemon=True)
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

    # --- Pack Charm & Bundle ---
    def run_charm_packing_and_bundling_in_thread(self):
        job_id = None
        zip_cleanup = None
        try:
            data = self.app_state["get_form_data"]()
            job_id = data.get("jobId")

            if not self._charm_temp_dir_path:
                raise RuntimeError(
                    "Charmcraft instance not properly initialized (temp dir not found)."
                )

            config_options_dicts = [
                opt.to_dict() for opt in data.get("configOptions", [])
            ]
            integration_ids = [
                integ.get("id") for integ in data.get("integrations", [])
            ]

            charm_gen_packer = CharmcraftGenerator(
                integration_ids,
                config_options_dicts,
                data.get("sourceProjectName", "my-charm"),
            )
            # Manually set the paths to the existing temp directory
            charm_gen_packer.temp_dir = self._charm_temp_dir_path
            charm_gen_packer.charm_project_path = os.path.join(
                charm_gen_packer.temp_dir, charm_gen_packer.project_name
            )

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
            self.pack_charm_bundle_button.disabled = False
        finally:
            # Clean up job directory
            if job_id and job_id in JOB_STORE:
                shutil.rmtree(TEMP_STORAGE_PATH / job_id, ignore_errors=True)
                del JOB_STORE[job_id]

            # Now we manually clean up the charm temp dir
            if self._charm_temp_dir_path:
                shutil.rmtree(self._charm_temp_dir_path, ignore_errors=True)
                self._charm_temp_dir_path = None

            self.page.update()

    def on_pack_charm_and_bundle(self, e):
        self.pack_charm_bundle_button.disabled = True
        self.edit_charm_button.disabled = True
        self.save_bundle_button.visible = False
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
