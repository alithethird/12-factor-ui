import flet as ft
from .AccordionStep import AccordionStep


class SelectIntegrations(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]

        # List of available integrations, now with a 'pre_selected' flag
        self.all_integrations = [
            {'id': 'prometheus', 'name': 'Prometheus', 'description': 'Monitoring & alerting', 'pre_selected': True},
            {'id': 'grafana', 'name': 'Grafana', 'description': 'Visualization dashboard', 'pre_selected': True},
            {'id': 'ingress', 'name': 'Ingress', 'description': 'Expose your app via HTTP/S', 'pre_selected': True},
            {'id': 'loki', 'name': 'Loki', 'description': 'Log aggregation system', 'pre_selected': True},
            {'id': 'postgresql', 'name': 'PostgreSQL', 'description': 'SQL database relation'},
            {'id': 'tracing', 'name': 'Tracing', 'description': 'Distributed tracing (e.g., OpenTelemetry)'},
            {'id': 'smtp', 'name': 'SMTP', 'description': 'Email sending integration'},
            {'id': 'openfga', 'name': 'OpenFGA', 'description': 'Fine-grained authorization'},
            {'id': 'oidc', 'name': 'OIDC', 'description': 'User authentication'},
        ]

        # --- Initialize Pre-selected Integrations ---
        # Ensure pre-selected items are in the global state from the start
        # We now store the entire integration dictionary, not just the ID
        initial_integrations = self.app_state["form_data"]["integrations"]
        initial_ids = {item['id'] for item in initial_integrations}

        for item in self.all_integrations:
            if item.get('pre_selected') and item['id'] not in initial_ids:
                initial_integrations.append(item)

        # This update is silent; it won't trigger a full page redraw immediately
        self.app_state["form_data"]["integrations"] = initial_integrations

        # --- Event Handlers ---
        def on_checkbox_change(e):
            integration_obj = e.control.data  # The data is now the full dictionary
            current_integrations = self.app_state["form_data"]["integrations"]
            current_ids = {item['id'] for item in current_integrations}

            if e.control.value:  # if checked
                if integration_obj['id'] not in current_ids:
                    current_integrations.append(integration_obj)
            else:  # if unchecked
                # Filter out the object with the matching id
                current_integrations = [item for item in current_integrations if item['id'] != integration_obj['id']]

            self.app_state["update_form_data"]({"integrations": current_integrations})

            # Update summary title
            count = len(current_integrations)
            if count > 0:
                self.update_summary(f"{count} Integration(s) Selected")
            else:
                self.update_summary(None)  # Reset to default title
            # No need for self.page.update() here, as update_form_data handles it

        def on_next(e):
            self.app_state["set_active_step"](4)

        # --- Build UI Controls ---
        integration_controls = []
        # Get a set of currently selected IDs for quick lookup
        selected_ids = {item['id'] for item in self.app_state["form_data"]["integrations"]}

        for item in self.all_integrations:
            is_preselected = item.get('pre_selected', False)
            checkbox = ft.Checkbox(
                label=f"{item['name']} - {item['description']}",
                value=(item['id'] in selected_ids),
                on_change=on_checkbox_change,
                data=item,  # Pass the entire dictionary as data
                disabled=is_preselected  # Disable the checkbox if it's pre-selected
            )
            integration_controls.append(checkbox)

        next_button = ft.ElevatedButton(
            "Next: Custom Configs",
            on_click=on_next,
            icon=ft.Icons.ARROW_FORWARD
        )

        # Use two Columns inside a Row for a robust 2-column layout.
        mid_point = (len(integration_controls) + 1) // 2
        column1_controls = integration_controls[:mid_point]
        column2_controls = integration_controls[mid_point:]

        integrations_layout = ft.Row(
            controls=[
                ft.Column(column1_controls, spacing=15, expand=True),
                ft.Column(column2_controls, spacing=15, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
            expand=True
        )

        content_control = ft.Column(
            [
                ft.Text("Select the integrations you want to add:", size=16),
                integrations_layout,
                next_button
            ],
            spacing=20,
        )

        # Call the parent constructor
        super().__init__(
            title="3. Select Integrations",
            step_number=3,
            app_state=app_state,
            content_control=content_control,
        )

