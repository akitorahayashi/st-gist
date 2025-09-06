import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    """
    テキストのベクトル化と検索を管理するクラス
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.texts = []
        self.embeddings = None
        self.is_creating = False
        self.last_error = None

    def create_embeddings(self, text: str, chunk_size=1000, chunk_overlap=200):
        """
        テキストをチャンクに分割し、ベクトル化して保存する

        Args:
            text: Scrapingされたコンテンツ
            chunk_size: 分割するチャンクのサイズ
            chunk_overlap: チャンク間のオーバーラップ
        """
        self.is_creating = True
        self.last_error = None
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
            self.texts = text_splitter.split_text(text)
            self.embeddings = self.model.encode(self.texts)
        except Exception as e:
            self.last_error = f"ベクトル化中にエラーが発生しました: {e}"
        finally:
            self.is_creating = False

    def search(self, query: str, top_k=5) -> str:
        """
        クエリに最も類似したテキストチャンクを検索し、結合して返す

        Args:
            query: ユーザーの質問文
            top_k: 取得する上位チャンク数

        Returns:
            結合された関連テキスト
        """
        if self.embeddings is None or not self.texts:
            return ""

        query_vec = self.model.encode([query])[0]
        similarities = cosine_similarity([query_vec], self.embeddings)[0]

        # 類似度が高い順にインデックスを取得
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # 類似度が0.3未満のものは除外する
        relevant_texts = [self.texts[i] for i in top_indices if similarities[i] >= 0.3]

        return "\n\n".join(relevant_texts)

    def reset(self):
        """
        ベクトルストアの状態をリセットする
        """
        self.texts = []
        self.embeddings = None
        self.is_creating = False
        self.last_error = None
