import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


class VectorStore:
    """
    Class to manage text vectorization and search
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
        self.texts = []
        self.embeddings = None
        self.is_creating = False
        self.last_error = None

    def create_embeddings(self, text: str, chunk_size=1000, chunk_overlap=200):
        """
        Split text into chunks, vectorize, and store

        Args:
            text: Scraped content
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
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
            self.last_error = f"Error occurred during vectorization: {e}"
        finally:
            self.is_creating = False

    def search(self, query: str, top_k=5) -> str:
        """Search for the most similar text chunks to the query and return the concatenated result"""
        if self.embeddings is None or not self.texts:
            return ""

        query_vec = self.model.encode([query])[0]

        # Calculate cosine similarity using numpy
        dot_product = np.dot(self.embeddings, query_vec)
        query_norm = np.linalg.norm(query_vec)
        embedding_norms = np.linalg.norm(self.embeddings, axis=1)
        similarities = dot_product / (query_norm * embedding_norms)

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
