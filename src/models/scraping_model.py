import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.protocols.models.scraping_model_protocol import ScrapingModelProtocol


class ScrapingModel(ScrapingModelProtocol):
    def __init__(self):
        self.content = None
        self.is_scraping = False

    def validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URLは http/https のみ対応しています。")
        if not parsed.hostname:
            raise ValueError("URLのホスト名が不正です。")
        if self._is_private_host(parsed.hostname):
            raise ValueError("指定のホストは許可されていません。")

    def _is_private_host(self, host: str) -> bool:
        addrs = set()
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                for info in socket.getaddrinfo(host, None, family):
                    addrs.add(info[4][0])
            except socket.gaierror:
                continue

        # DNS解決できない場合（架空のホスト）
        if not addrs:
            raise ValueError(
                f"指定されたホスト '{host}' が見つかりません。URLを確認してください。"
            )

        for addr in addrs:
            ip = ipaddress.ip_address(addr.split("%")[0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                return True
        return False

    def scrape(self, url: str, timeout=(30, 90)) -> str:
        self.is_scraping = True
        try:
            self.validate_url(url)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            try:
                response = requests.get(
                    url, headers=headers, timeout=timeout, allow_redirects=False
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise ValueError(f"コンテンツ取得に失敗しました: {e}") from e

            # 明らかに非 HTML のレスポンスは早期リターン
            ctype = (response.headers.get("Content-Type") or "").lower()
            if not ("html" in ctype or ctype.startswith("text/")):
                self.content = ""
                return ""

            soup = BeautifulSoup(response.content, "html.parser")
            for element in soup(
                ["script", "style", "header", "footer", "nav", "aside"]
            ):
                element.decompose()
            if soup.body:
                content = soup.body.get_text(separator=" ", strip=True)
            else:
                content = ""

            self.content = content
            return content
        except Exception as e:
            # 予期しないエラーの場合
            if not isinstance(e, ValueError):
                raise ValueError(f"予期しないエラーが発生しました: {str(e)}") from e
            raise
        finally:
            self.is_scraping = False

    def reset(self):
        """Reset the scraping model state."""
        self.content = None
        self.is_scraping = False
