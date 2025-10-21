import flet as ft
from .AccordionStep import AccordionStep


class SelectIntegrations(AccordionStep):
    def __init__(self, app_state):
        self.app_state = app_state
        self.page = self.app_state["page"]

        # List of available integrations
        self.all_integrations = [
            {'id': 'prometheus', 'name': 'Prometheus', 'description': 'Monitoring & alerting'},
            {'id': 'grafana', 'name': 'Grafana', 'description': 'Visualization dashboard'},
            {'id': 'ingress', 'name': 'Ingress', 'description': 'Expose your app via HTTP/S'},
            {'id': 'loki', 'name': 'Loki', 'description': 'Log aggregation system'},
            {'id': 'postgresql', 'name': 'PostgreSQL', 'description': 'SQL database relation'},
            {'id': 'tracing', 'name': 'Tracing', 'description': 'Distributed tracing (e.g., OpenTelemetry)'},
            {'id': 'smtp', 'name': 'SMTP', 'description': 'Email sending integration'},
            {'id': 'openfga', 'name': 'OpenFGA', 'description': 'Fine-grained authorization'},
            {'id': 'oidc', 'name': 'OIDC', 'description': 'User authentication'},
        ]

        # --- Event Handlers ---
        def on_checkbox_change(e):
            integration_id = e.control.data
            current_integrations = self.app_state["form_data"]["integrations"]

            if e.control.value:  # if checked
                if integration_id not in current_integrations:
                    current_integrations.append(integration_id)
            else:  # if unchecked
                if integration_id in current_integrations:
                    current_integrations.remove(integration_id)

            self.app_state["update_form_data"]({"integrations": current_integrations})

            # Update summary title
            count = len(current_integrations)
            if count > 0:
                self.update_summary(f"{count} Integration(s) Selected")
            else:
                self.update_summary(None)  # Reset to default title
            self.page.update()

        def on_next(e):
            self.app_state["set_active_step"](4)

        # --- Build UI Controls ---
        integration_controls = []
        for item in self.all_integrations:
            # The Checkbox is now the clickable control itself
            checkbox = ft.Checkbox(
                label=f"{item['name']} - {item['description']}",
                value=(item['id'] in self.app_state["form_data"]["integrations"]),
                on_change=on_checkbox_change,
                data=item['id']
            )
            integration_controls.append(checkbox)

        next_button = ft.ElevatedButton(
            "Next: Custom Configs",
            on_click=on_next,
            icon=ft.Icons.ARROW_FORWARD
        )

        # Instead of GridView, use two Columns inside a Row for a robust 2-column layout.

        # Split the controls into two lists for the two columns
        mid_point = (len(integration_controls) + 1) // 2
        column1_controls = integration_controls[:mid_point]
        column2_controls = integration_controls[mid_point:]

        integrations_layout = ft.Row(
            controls=[
                ft.Column(column1_controls, spacing=15, expand=True, wrap=True),
                ft.Column(column2_controls, spacing=15, expand=True, wrap=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
            # Let the row expand to fill the available width
            expand=True
        )

        content_control = ft.Column(
            [
                ft.Text("Select the integrations you want to add:", size=16),
                integrations_layout,  # Add the Row/Column layout here
                next_button
            ],
            spacing=20,  # Increased spacing for a better look
        )
        # --- END FIX ---

        # Call the parent constructor
        super().__init__(
            title="3. Select Integrations",
            step_number=3,
            app_state=app_state,
            content_control=content_control,
        )