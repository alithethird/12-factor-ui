import flet as ft
from .AccordionStep import AccordionStep


# Define the structure for a single config option
class ConfigOption:
    def __init__(self, key: str, type: str, value: str, is_optional: bool):
        self.key = key
        self.type = type
        self.value = value
        self.is_optional = is_optional

    def to_dict(self):
        return {
            "key": self.key,
            "type": self.type,
            "value": self.value,
            "isOptional": self.is_optional,
        }


class ConfigOptions(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]

        # --- UI Controls for adding new options ---
        self.new_key_field = ft.TextField(label="Key", hint_text="e.g., secret-key", expand=2)
        self.new_type_dropdown = ft.Dropdown(
            label="Type",
            options=[
                ft.dropdown.Option("string"),
                ft.dropdown.Option("bool"),
                ft.dropdown.Option("int"),
                ft.dropdown.Option("float"),
                ft.dropdown.Option("secret"),
            ],
            value="string",
            expand=1,
        )
        self.new_optional_checkbox = ft.Checkbox(label="Optional", value=False)
        self.new_value_field = ft.TextField(label="Default Value", hint_text="leave empty if not optional", expand=2)
        self.error_text = ft.Text(color=ft.Colors.RED, visible=False)

        # This will hold the visual list of added options
        self.options_list_view = ft.Column(spacing=5)

        # --- Event Handlers ---
        def on_add_option(e):
            self.error_text.visible = False
            key = self.new_key_field.value.strip()
            value = self.new_value_field.value.strip()
            is_optional = self.new_optional_checkbox.value

            # Validation
            if not key:
                self.error_text.value = "Error: Key cannot be empty."
                self.error_text.visible = True
                self.page.update()
                return

            if any(opt.key.lower() == key.lower() for opt in self.app_state["form_data"]["configOptions"]):
                self.error_text.value = "Error: Key must be unique."
                self.error_text.visible = True
                self.page.update()
                return

            if not is_optional and value != "":
                self.error_text.value = "Error: Required configs cannot have a default value."
                self.error_text.visible = True
                self.page.update()
                return

            # Add to state and update UI
            new_option = ConfigOption(
                key=key,
                type=self.new_type_dropdown.value,
                value=value,
                is_optional=is_optional,
            )
            current_options = self.app_state["form_data"]["configOptions"]
            current_options.append(new_option)
            self.app_state["update_form_data"]({"configOptions": current_options})

            # Reset fields
            self.new_key_field.value = ""
            self.new_value_field.value = ""
            self.new_optional_checkbox.value = False

            self.update_options_list()
            self.update_summary_title()
            self.page.update()

        def on_next(e):
            self.app_state["set_active_step"](5)

        # --- UI Layout ---
        add_button = ft.ElevatedButton("Add", on_click=on_add_option, icon=ft.Icons.ADD)

        add_row = ft.Row(
            controls=[
                self.new_key_field,
                self.new_type_dropdown,
                self.new_optional_checkbox,
                self.new_value_field,
                add_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        next_button = ft.ElevatedButton("Next: Generate Files", on_click=on_next, icon=ft.Icons.ARROW_FORWARD)

        content_control = ft.Column(
            [
                ft.Text("Enter any custom config options for your charm:", size=16),
                ft.Divider(),
                self.options_list_view,  # Placeholder for the list
                ft.Divider(),
                add_row,
                self.error_text,
                next_button,
            ],
            spacing=15,
        )

        self.update_options_list()  # Initial population of the list

        super().__init__(
            title="4. Custom Config Options",
            step_number=4,
            app_state=app_state,
            content_control=content_control,
        )

    def update_options_list(self):
        """Re-renders the list of added config options."""
        self.options_list_view.controls.clear()

        current_options = self.app_state["form_data"]["configOptions"]
        if not current_options:
            self.options_list_view.controls.append(
                ft.Text("No config options added yet.", italic=True, color=ft.Colors.BLACK54))
            return

        # Header row
        self.options_list_view.controls.append(
            ft.Row([
                ft.Text("Key", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Type", weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Optional", weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Default Value", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Action", weight=ft.FontWeight.BOLD, width=80),
            ])
        )

        for option in current_options:
            def on_remove(e):
                opt_to_remove = e.control.data
                updated_options = [o for o in self.app_state["form_data"]["configOptions"] if
                                   o.key != opt_to_remove.key]
                self.app_state["update_form_data"]({"configOptions": updated_options})
                self.update_options_list()
                self.update_summary_title()
                self.page.update()

            row = ft.Row(
                controls=[
                    ft.Text(option.key, expand=2),
                    ft.Text(option.type, expand=1),
                    ft.Text("Yes" if option.is_optional else "No", expand=1),
                    ft.Text(option.value, expand=2),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED,
                        on_click=on_remove,
                        data=option,
                        tooltip="Remove",
                        width=80,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            self.options_list_view.controls.append(row)

    def update_summary_title(self):
        count = len(self.app_state["form_data"]["configOptions"])
        if count > 0:
            self.update_summary(f"{count} Config Option(s) Added")
        else:
            self.update_summary(None)
