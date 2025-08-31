from typing import Protocol


class ScrapingProtocol(Protocol):
    """
    Protocol for web scraping services.
    """
    
    def scrape(self, url: str, timeout: tuple = (10, 30)) -> str:
        """
        Scrape content from a web page.

        Args:
            url: The URL to scrape.
            timeout: Request timeout tuple (connect, read).

        Returns:
            Extracted text content from the web page.
            
        Raises:
            ValueError: If URL is invalid or scraping fails.
        """
        ...
    
    def validate_url(self, url: str) -> None:
        """
        Validate URL format and security.

        Args:
            url: The URL to validate.

        Raises:
            ValueError: If URL is invalid or not allowed.
        """
        ...