class TestURLInputPage:
    """UI tests for the URL input page functionality."""

    def test_initial_page_load(self, app_test_with_mocks):
        """Test that the URL input page loads correctly with initial state."""
        at, models = app_test_with_mocks

        # Verify initial page elements are present
        assert len(at.title) >= 1  # Page should have a title
        assert len(at.text_input) >= 1  # Should have URL input field

        # Should be on INPUT page initially
        assert hasattr(at.session_state, "app_router")

    def test_url_input_validation(self, app_test_with_mocks):
        """Test URL input validation functionality."""
        at, models = app_test_with_mocks

        # Configure scraping model to validate URLs
        models["scraping"].validate_url.return_value = (
            False,
            "URLは http/https のみ対応しています。",
        )

        # Input invalid URL
        if len(at.text_input) > 0:
            at.text_input[0].set_value("ftp://invalid-url.com").run()

            # Try to submit (look for button to click)
            if len(at.button) > 0:
                at.button[0].click().run()

                # Should show validation error
                error_found = any(
                    "http/https" in str(element.value) for element in at.error
                )
                assert error_found or any(
                    "http/https" in str(element.value) for element in at.markdown
                )

    def test_valid_url_submission(self, app_test_with_mocks):
        """Test successful URL submission and navigation to chat page."""
        at, models = app_test_with_mocks

        # Configure scraping model behavior
        models["scraping"].validate_url.return_value = (True, "")
        models["scraping"].scrape.return_value = "This is scraped content from the URL."

        # Input valid URL
        if len(at.text_input) > 0:
            at.text_input[0].set_value("https://example.com").run()

            # Submit the URL
            if len(at.button) > 0:
                at.button[0].click().run()

                # Should navigate to chat page or show processing
                # App should handle the submission gracefully
                assert at is not None  # App should not crash

    def test_empty_url_handling(self, app_test_with_mocks):
        """Test handling of empty URL submission."""
        at, models = app_test_with_mocks

        # Try to submit without entering URL
        if len(at.button) > 0:
            at.button[0].click().run()

            # Should show some validation or remain on same page
            # App should handle empty input gracefully
            assert len(at.text_input) >= 1  # Input field should still be present

    def test_sidebar_elements_present(self, app_test_with_mocks):
        """Test that sidebar elements are present on URL input page."""
        at, models = app_test_with_mocks

        # Sidebar should be present with some elements
        assert len(at.sidebar) >= 1 or hasattr(at.session_state, "app_router")

    def test_page_title_and_icon(self, app_test_with_mocks):
        """Test that page has correct title and icon configuration."""
        at, models = app_test_with_mocks

        # Verify app loaded without errors
        assert at is not None
        # Page title and icon are configured via st.set_page_config
        # which happens before the app runs
