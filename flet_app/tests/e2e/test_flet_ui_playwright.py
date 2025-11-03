"""Playwright-based end-to-end tests for the Flet UI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest


@pytest.mark.e2e
@pytest.mark.web
@pytest.mark.slow
class TestFletUIPageLoading:
    """Test suite for Flet web app page loading and basic functionality."""

    def test_page_loads_and_shows_canvas(self, page):
        """Test: Verify Flet app page loads and renders canvas."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)  # Allow Flet to fully render
        
        # Verify canvas is visible (Flet renders to canvas in web mode)
        canvas = page.locator("canvas").first
        assert canvas.is_visible(), "Flet canvas should be visible"
        
        # Verify page URL is correct
        assert "127.0.0.1:8000" in page.url, f"Expected URL to contain 127.0.0.1:8000, got '{page.url}'"
    
    def test_canvas_is_interactive(self, page):
        """Test: Verify the canvas is interactive (clickable)."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        
        # Get canvas bounding box to click on it
        bbox = canvas.bounding_box()
        assert bbox is not None, "Canvas bounding box should be available"
        
        # Click in the upper portion of canvas (where framework cards should be)
        # Coordinates are approximate for the first card area
        page.mouse.click(150, 150)
        
        # Wait for response
        page.wait_for_timeout(500)
        
        # Page should still be responsive
        assert page.locator("canvas").first.is_visible()


@pytest.mark.e2e
@pytest.mark.web
@pytest.mark.slow
class TestFletUIFrameworkSelection:
    """Test suite for framework selection workflow."""

    def test_framework_card_interaction_flask(self, page):
        """Test: Interact with Flask framework card."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        bbox = canvas.bounding_box()
        
        # Flask card is typically in the first column of the grid
        # Approximate coordinates for Flask card (upper-left area of grid)
        flask_x = 150
        flask_y = 200
        
        page.mouse.click(flask_x, flask_y)
        page.wait_for_timeout(1000)
        
        # Verify page is still responsive
        assert page.locator("canvas").first.is_visible()
    
    def test_framework_card_interaction_django(self, page):
        """Test: Interact with Django framework card."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        bbox = canvas.bounding_box()
        
        # Django card is typically in the second position of the grid
        django_x = 300
        django_y = 200
        
        page.mouse.click(django_x, django_y)
        page.wait_for_timeout(1000)
        
        # Verify page is still responsive
        assert page.locator("canvas").first.is_visible()
    
    def test_framework_card_interaction_fastapi(self, page):
        """Test: Interact with FastAPI framework card."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        bbox = canvas.bounding_box()
        
        # FastAPI card is typically in the third position of the grid
        fastapi_x = 450
        fastapi_y = 200
        
        page.mouse.click(fastapi_x, fastapi_y)
        page.wait_for_timeout(1000)
        
        # Verify page is still responsive
        assert page.locator("canvas").first.is_visible()
    
    def test_framework_card_interaction_go(self, page):
        """Test: Interact with Go framework card."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        bbox = canvas.bounding_box()
        
        # Go card is typically in the fourth position of the grid
        go_x = 600
        go_y = 200
        
        page.mouse.click(go_x, go_y)
        page.wait_for_timeout(1000)
        
        # Verify page is still responsive
        assert page.locator("canvas").first.is_visible()
    
    def test_framework_card_interaction_expressjs(self, page):
        """Test: Interact with Express.js framework card."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        bbox = canvas.bounding_box()
        
        # Express.js card is typically in the fifth position of the grid
        expressjs_x = 750
        expressjs_y = 200
        
        page.mouse.click(expressjs_x, expressjs_y)
        page.wait_for_timeout(1000)
        
        # Verify page is still responsive
        assert page.locator("canvas").first.is_visible()
    
    def test_framework_card_interaction_springboot(self, page):
        """Test: Interact with Spring Boot framework card."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        bbox = canvas.bounding_box()
        
        # Spring Boot card would be in the second row if visible
        # or might wrap depending on screen size
        springboot_x = 150
        springboot_y = 350
        
        page.mouse.click(springboot_x, springboot_y)
        page.wait_for_timeout(1000)
        
        # Verify page is still responsive
        assert page.locator("canvas").first.is_visible()


@pytest.mark.e2e
@pytest.mark.web
@pytest.mark.slow
class TestFletUIMultipleInteractions:
    """Test suite for multiple framework interactions and navigation."""

    def test_select_multiple_frameworks_sequentially(self, page):
        """Test: Select multiple frameworks in sequence."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        
        # Click Flask first
        page.mouse.click(150, 200)
        page.wait_for_timeout(500)
        
        # Click Django
        page.mouse.click(300, 200)
        page.wait_for_timeout(500)
        
        # Click FastAPI
        page.mouse.click(450, 200)
        page.wait_for_timeout(500)
        
        # Page should remain responsive
        assert page.locator("canvas").first.is_visible()
    
    def test_rapid_framework_selection(self, page):
        """Test: Rapidly click different framework cards."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        
        # Rapidly select different frameworks
        for x in [150, 300, 450, 600, 750]:
            page.mouse.click(x, 200)
            page.wait_for_timeout(200)
        
        # Page should handle rapid clicks gracefully
        assert page.locator("canvas").first.is_visible()
    
    def test_click_same_framework_twice(self, page):
        """Test: Click the same framework twice."""
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        canvas = page.locator("canvas").first
        
        # Click Flask twice
        page.mouse.click(150, 200)
        page.wait_for_timeout(500)
        
        page.mouse.click(150, 200)
        page.wait_for_timeout(500)
        
        # Page should handle double-click gracefully
        assert page.locator("canvas").first.is_visible()
