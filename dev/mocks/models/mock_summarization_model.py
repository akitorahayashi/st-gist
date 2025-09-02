import asyncio

from src.protocols.models.summarization_model_protocol import SummarizationModelProtocol


class MockSummarizationModel(SummarizationModelProtocol):
    """
    Mock summarization model for testing and development.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # Not used in mock but kept for compatibility

    async def summarize(self, text: str, max_chars: int = 10000) -> str:
        """
        Mock summarization that generates a structured summary.

        Args:
            text: The text to summarize
            max_chars: Maximum characters to process (ignored in mock)

        Returns:
            A formatted mock summary
        """
        if not text or not text.strip():
            return ""

        # Simulate processing time
        await asyncio.sleep(0.5)

        # Extract some keywords from the text for a more realistic mock
        words = text.lower().split()
        important_words = [w for w in words if len(w) > 4 and w.isalpha()][:5]

        # Create a mock summary with the expected format
        # Generate different points based on content
        point1 = self._generate_point(text, "主要な内容")
        point2 = (
            self._generate_point(text, "重要なポイント")
            if point1 != self._generate_point(text, "重要なポイント")
            else f"追加の{self._generate_fallback_point(text)}"
        )
        point3 = (
            self._generate_point(text, "特徴的な要素")
            if point1 != self._generate_point(text, "特徴的な要素")
            else f"詳細な{self._generate_fallback_point(text)}"
        )

        summary = f"""タイトル: {self._generate_title(text, important_words)}

要点:
• {point1}
• {point2}
• {point3}"""

        return summary

    def _generate_title(self, text: str, keywords: list) -> str:
        """Generate a mock title based on text content."""
        if "example.com" in text.lower():
            return "Exampleサイトの概要と機能紹介"
        elif "news" in text.lower() or "breaking" in text.lower():
            return "最新技術ニュースとAI分野の動向"
        elif "blog" in text.lower() or "journey" in text.lower():
            return "ソフトウェア開発者の個人ブログ"
        elif keywords:
            return f"「{keywords[0]}」に関する情報とその詳細"
        else:
            return "ウェブページの内容とその要約"

    def _generate_point(self, text: str, context: str) -> str:
        """Generate a mock bullet point based on text content."""
        # Check for specific keywords in order of priority
        if "ai" in text.lower() and ("model" in text.lower() or "news" in text.lower()):
            return "AI技術の進歩により、コーディングタスクで40%の性能向上を実現"
        elif "developer" in text.lower() or "software development" in text.lower():
            return "フルスタック開発者による実践的な技術ブログとプログラミング経験"
        elif "technology company" in text.lower():
            return "革新的な技術ソリューションを提供する会社の概要と特徴"
        elif "features" in text.lower():
            return (
                "使いやすいインターフェースと高速な読み込み時間を特徴とするウェブサイト"
            )
        else:
            return f"ページの{context}について詳細な情報と実用的なアドバイスを提供"

    def _generate_fallback_point(self, text: str) -> str:
        """Generate a fallback point when main points are similar."""
        if "news" in text.lower():
            return "技術情報の分析"
        elif "blog" in text.lower():
            return "開発経験の共有"
        else:
            return "サイトの機能解説"
