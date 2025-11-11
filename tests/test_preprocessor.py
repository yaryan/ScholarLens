"""
Text Preprocessor Module

Handles:
- Normalization
- Tokenization
- Stopword removal
- Lemmatization
- Text chunking

Author: ScholarLens Project
"""

import re
import logging
import spacy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Text Preprocessing utility class"""

    def __init__(self, model_name: str = "en_core_web_md"):
        """Initialize the spaCy NLP model"""
        try:
            self.nlp = spacy.load(model_name, disable=["ner"])
            logger.info(f"✓ Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"⚠ Model '{model_name}' not found. Downloading...")
            from spacy.cli import download

            download(model_name)
            self.nlp = spacy.load(model_name, disable=["ner"])
            logger.info(f"✓ Downloaded and loaded spaCy model: {model_name}")

    # ---------------------------------------------------------------------
    # 🧹 Normalization
    # ---------------------------------------------------------------------
    def normalize_text(self, text: str) -> str:
        """Lowercase, remove special characters and extra whitespace"""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ---------------------------------------------------------------------
    # 🔤 Tokenization
    # ---------------------------------------------------------------------
    def tokenize(self, text: str):
        """Tokenize text into a list of tokens"""
        doc = self.nlp(text)
        tokens = [token.text for token in doc if not token.is_space]
        return tokens

    # ---------------------------------------------------------------------
    # 🧠 Lemmatization
    # ---------------------------------------------------------------------
    def lemmatize(self, text: str):
        """Return lemmatized tokens"""
        doc = self.nlp(text)
        lemmas = [token.lemma_ for token in doc if not token.is_space]
        return lemmas

    # ---------------------------------------------------------------------
    # 🚫 Stopword removal
    # ---------------------------------------------------------------------
    def remove_stopwords(self, text: str):
        """Remove stopwords from text"""
        doc = self.nlp(text)
        filtered_tokens = [token.text for token in doc if not token.is_stop and not token.is_space]
        return " ".join(filtered_tokens)

    # ---------------------------------------------------------------------
    # ✂️ Text Chunking
    # ---------------------------------------------------------------------
    def chunk_text(self, text: str, chunk_size: int = 200, overlap: int = 50):
        """
        Chunk text efficiently by token count.

        Args:
            text (str): Input text.
            chunk_size (int): Max number of tokens per chunk.
            overlap (int): Number of overlapping tokens between chunks.

        Returns:
            list[dict]: List of text chunks with metadata.
        """
        doc = self.nlp(text)
        return self._chunk_by_tokens(doc, chunk_size, overlap)

    def _chunk_by_tokens(self, doc, chunk_size: int, overlap: int):
        """Internal: Efficient memory-safe chunking by token list."""
        chunks = []
        tokens = [t.text for t in doc]
        total_tokens = len(tokens)

        for i in range(0, total_tokens, chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = " ".join(chunk_tokens)

            chunks.append({
                "text": chunk_text,
                "num_tokens": len(chunk_tokens),
                "start_token": i,
                "end_token": i + len(chunk_tokens)
            })

        return chunks


# -------------------------------------------------------------------------
# 🧪 Simple usage example (manual test)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    pre = TextPreprocessor()

    sample_text = "This is a sample text document for testing the text preprocessor module."
    print("\nNormalized:", pre.normalize_text(sample_text))
    print("Tokens:", pre.tokenize(sample_text))
    print("Lemmas:", pre.lemmatize(sample_text))
    print("Without stopwords:", pre.remove_stopwords(sample_text))

    chunks = pre.chunk_text(" ".join(["word"] * 100), chunk_size=30, overlap=5)
    print(f"\nChunks created: {len(chunks)}")
    print("First chunk:", chunks[0])
