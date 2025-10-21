import flet as ft
from .AccordionStep import AccordionStep

class SelectFramework(AccordionStep):
    def __init__(self, app_state):
        # 1. Define the content for this specific step first
        frameworks = [
            {'id': 'flask', 'name': 'Flask', 'logo_path': 'static/logos/flask.svg'},
            {'id': 'django', 'name': 'Django', 'logo_path': 'static/logos/django.svg'},
            {'id': 'fastapi', 'name': 'FastAPI', 'logo_path': 'static/logos/fastapi.svg'},
            {'id': 'go', 'name': 'Go', 'logo_path': 'static/logos/go.svg'},
            {'id': 'expressjs', 'name': 'Express.js', 'logo_path': 'static/logos/expressjs.svg'},
            {'id': 'springboot', 'name': 'Spring Boot', 'logo_path': 'static/logos/spring-boot.svg'},
        ]

        def on_framework_select(e):
            fw_id = e.control.data["id"]
            fw_name = e.control.data["name"]
            app_state["update_form_data"]({"framework": fw_id, "frameworkName": fw_name})
            self.update_summary(f"Framework: {fw_name}")
            app_state["set_active_step"](2)

        cards = []
        for fw in frameworks:
            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Image(src=fw['logo_path'], width=40, height=40, fit=ft.ImageFit.CONTAIN),
                        ft.Text(fw['name'], weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                    spacing=5,
                ),
                padding=20,
                alignment=ft.alignment.center,
                border=ft.border.all(2, ft.Colors.BLACK12),
                border_radius=8,
                on_click=on_framework_select,
                data=fw,
                ink=True,
                tooltip=f"Select {fw['name']}",
            )
            cards.append(card)

        content_control = ft.Column([
            ft.Text("Select your project's framework:", size=16),
            ft.GridView(
                cards,
                expand=False,
                runs_count=5,
                max_extent=150,
                child_aspect_ratio=1.0,
                spacing=10,
                run_spacing=10,
            ),
        ], spacing=15)

        # 2. Call the parent constructor with the title, step number, and the content
        super().__init__(
            title="1. Select Framework",
            step_number=1,
            app_state=app_state,
            content_control=content_control
        )

    def before_update(self):
        """Handle component-specific updates before re-rendering."""
        # Update the selected card's background color
        selected_fw_id = self.app_state["get_form_data"]()["framework"]
        grid_view = self.content_control.controls[1] # GridView is the second control
        for card in grid_view.controls:
            if card.data["id"] == selected_fw_id:
                card.bgcolor = ft.Colors.BLUE_50
            else:
                card.bgcolor = ft.Colors.WHITE
        
        # Call the parent's before_update to handle visibility and styling
        super().before_update()
