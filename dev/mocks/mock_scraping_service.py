from typing import Dict


class MockScrapingService:
    """
    Mock scraping service for testing and development.
    """
    
    def __init__(self):
        self.mock_content: Dict[str, str] = {
            "https://example.com": """
                Example Website
                
                This is a sample website for testing purposes.
                
                Features:
                - Easy to use interface
                - Fast loading times
                - Responsive design
                - Modern technology stack
                
                About Us:
                We are a technology company focused on creating innovative solutions
                for modern web development challenges.
                
                Contact:
                Email: info@example.com
                Phone: 123-456-7890
            """,
            "https://news.example.com": """
                Tech News Today
                
                Breaking: New AI Model Released
                
                A new large language model has been released today, showing
                significant improvements in reasoning and code generation.
                
                Key Features:
                - 40% better performance on coding tasks
                - Improved multilingual support
                - Better reasoning capabilities
                - More efficient training process
                
                Market Impact:
                Industry experts predict this will accelerate AI adoption
                across various sectors including healthcare, finance, and education.
            """,
            "https://blog.example.com": """
                Personal Blog
                
                My Journey in Software Development
                
                Welcome to my blog where I share my experiences as a software developer.
                
                Recent Posts:
                1. "Learning Python in 2024"
                2. "Best Practices for API Design"
                3. "Introduction to Machine Learning"
                4. "Building Scalable Web Applications"
                
                About the Author:
                I'm a full-stack developer with 5 years of experience in building
                web applications using modern technologies like React, Python, and Node.js.
            """
        }
    
    def validate_url(self, url: str) -> None:
        """Mock URL validation - always passes for test URLs."""
        if not url.startswith(("http://", "https://")):
            raise ValueError("URLは http/https のみ対応しています。")
        if "blocked.com" in url:
            raise ValueError("指定のホストは許可されていません。")
    
    def scrape(self, url: str, timeout: tuple = (10, 30)) -> str:
        """
        Mock scraping that returns predefined content.
        
        Args:
            url: The URL to scrape
            timeout: Ignored in mock
            
        Returns:
            Mock content for the URL
        """
        self.validate_url(url)
        
        # Return specific content if available, otherwise generic content
        if url in self.mock_content:
            return self.mock_content[url].strip()
        
        # Generate generic content for unknown URLs
        return f"""
        Website Content
        
        This is mock content for: {url}
        
        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
        Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        
        Key Points:
        - Point one about the website content
        - Point two with important information
        - Point three summarizing main topics
        
        Additional Information:
        This is a mock response generated for testing purposes.
        The actual website content would appear here in a real scenario.
        """.strip()