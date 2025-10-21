import flet as ft

class AccordionStep(ft.Column):
    """A reusable accordion control that uses the modern Flet API."""
    def __init__(self, title, step_number, app_state, content_control):
        super().__init__()
        self.title_text = title
        self.step_number = step_number
        self.app_state = app_state
        self.content_control = content_control
        self.summary_title = None
        self.spacing = 0 # No space between header and content

        # --- Control Setup ---
        self.title_display = ft.Text(self.title_text, weight=ft.FontWeight.BOLD)
        self.check_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, opacity=0)

        self.header = ft.Container(
            content=ft.Row(
                [self.title_display, self.check_icon],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=15,
            border_radius=5,
            on_click=self.header_clicked,
            ink=True,
        )

        self.content_area = ft.Column(
            [self.content_control],
            visible=False, # Initially hidden
            spacing=10
        )
        
        self.controls = [self.header, self.content_area]

    def header_clicked(self, e):
        """Handle click events on the accordion header."""
        if self.step_number <= self.app_state["active_step"]:
            self.app_state["set_active_step"](self.step_number)

    def update_summary(self, new_summary):
        """Update the summary text when a step is completed."""
        self.summary_title = new_summary

    def before_update(self):
        """
        This method is called by Flet before re-rendering.
        We use it to update the visual state based on the global app_state.
        """
        is_active = self.app_state["active_step"] == self.step_number
        is_completed = self.app_state["active_step"] > self.step_number

        header_color = ft.Colors.WHITE
        title_color = ft.Colors.BLACK
        self.check_icon.opacity = 0
        self.content_area.visible = is_active
        
        if is_active:
            header_color = ft.Colors.BLUE_50
        if is_completed:
            header_color = ft.Colors.GREEN_50
            title_color = ft.Colors.GREEN_800
            self.check_icon.opacity = 1

        self.header.bgcolor = header_color
        self.title_display.color = title_color
        self.title_display.value = self.summary_title if is_completed and self.summary_title else self.title_text
