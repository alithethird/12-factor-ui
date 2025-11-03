"""Helper utilities for Playwright-based Flet UI testing."""


class FletPageHelper:
    """Helper class to interact with Flet UI components via Playwright."""
    
    def __init__(self, page):
        """Initialize with a Playwright page object."""
        self.page = page
    
    def find_button(self, text: str):
        """Find a button by its text content."""
        return self.page.locator(f"button:has-text('{text}')")
    
    def find_card(self, text: str):
        """Find a card/container by its text content."""
        # Flet cards are typically containers with text
        return self.page.locator(f"div:has-text('{text}')")
    
    def click_button(self, text: str):
        """Click a button by its text."""
        button = self.find_button(text)
        button.click()
    
    def click_card(self, text: str):
        """Click a card/container by its text."""
        card = self.find_card(text)
        card.click()
    
    def get_text(self, text: str):
        """Get text from an element."""
        return self.page.locator(f"text='{text}'")
    
    def fill_input(self, placeholder: str, text: str):
        """Fill an input field by placeholder."""
        self.page.fill(f"input[placeholder='{placeholder}']", text)
    
    def upload_file(self, selector: str, file_path: str):
        """Upload a file to a file input."""
        self.page.locator(selector).set_input_files(file_path)
    
    def wait_for_text(self, text: str, timeout: int = 5000):
        """Wait for text to appear on the page."""
        self.page.locator(f"text='{text}'").wait_for(state="visible", timeout=timeout)
    
    def wait_for_element(self, selector: str, timeout: int = 5000):
        """Wait for an element to appear."""
        self.page.locator(selector).wait_for(state="visible", timeout=timeout)
    
    def is_visible(self, text: str) -> bool:
        """Check if text is visible on the page."""
        try:
            element = self.page.locator(f"text='{text}'")
            return element.is_visible()
        except Exception:
            return False
    
    def is_button_enabled(self, text: str) -> bool:
        """Check if a button is enabled."""
        button = self.find_button(text)
        return button.is_enabled()
    
    def screenshot(self, path: str):
        """Take a screenshot of the page."""
        self.page.screenshot(path=path)
