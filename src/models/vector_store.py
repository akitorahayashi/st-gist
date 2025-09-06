import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    """
    Class to manage text vectorization and search
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.texts = []
        self.embeddings = None
        self.is_creating = False
        self.last_error = None
        self.is_initialized = False

    def _ensure_initialized(self):
        """Initialize the model if not already initialized"""
        if not self.is_initialized:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
            self.is_initialized = True

    def create_embeddings(self, text: str, chunk_size=1000, chunk_overlap=200):
        """
        Split text into chunks, vectorize, and store

        Args:
            text: Scraped content
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
        """
        self._ensure_initialized()
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
            self.last_error = f"Error occurred during vectorization: {e}"
        finally:
            self.is_creating = False

    def search(self, query: str, top_k=5) -> str:
        """Search for the most similar text chunks to the query and return the concatenated result"""
        if self.embeddings is None or not self.texts:
            return ""

        self._ensure_initialized()
        query_vec = self.model.encode([query])[0]
        similarities = cosine_similarity([query_vec], self.embeddings)[0]

        # Get top-k indices sorted by similarity in descending order
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Always return top-k chunks
        relevant_texts = [self.texts[i] for i in top_indices]
        return "\n\n".join(relevant_texts)

    def reset(self):
        """
        Reset the state of the vector store
        """
        self.texts = []
        self.embeddings = None
        self.is_creating = False
        self.last_error = None
        # Keep the model cached
