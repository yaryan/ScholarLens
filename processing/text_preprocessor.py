"""
Text Preprocessor for Research Papers

This module provides text preprocessing capabilities including:
- Tokenization
- Text chunking with overlap
- Normalization
- Stopword removal
- Lemmatization
"""

import spacy
import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextPreprocessor:
    """
    Text preprocessing pipeline for research papers.

    Features:
    - Tokenization with spaCy
    - Text chunking for transformer models
    - Multiple normalization options
    - Efficient processing
    """

    def __init__(self, model_name: str = 'en_core_web_md'):
        """
        Initialize text preprocessor.

        Args:
            model_name: spaCy model to use
        """
        try:
            self.nlp = spacy.load(model_name)
            # Disable unnecessary components for speed
            self.nlp.select_pipes(enable=['tok2vec', 'tagger', 'lemmatizer'])

            logger.info(f"✓ Loaded spaCy model: {model_name}")

        except OSError:
            logger.error(f"✗ Model '{model_name}' not found. Run: python -m spacy download {model_name}")
            raise

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        doc = self.nlp(text)
        tokens = [token.text for token in doc if not token.is_space]

        logger.debug(f"Tokenized into {len(tokens)} tokens")
        return tokens

    def remove_stopwords(self, text: str) -> str:
        """
        Remove common stopwords.

        Args:
            text: Input text

        Returns:
            Text with stopwords removed
        """
        doc = self.nlp(text)
        tokens = [token.text for token in doc
                  if not token.is_stop and not token.is_punct and not token.is_space]

        return " ".join(tokens)

    def lemmatize(self, text: str) -> str:
        """
        Convert words to base forms (lemmatization).

        Args:
            text: Input text

        Returns:
            Lemmatized text
        """
        doc = self.nlp(text)
        lemmas = [token.lemma_ for token in doc if not token.is_space]

        return " ".join(lemmas)

    def chunk_text(
            self,
            text: str,
            chunk_size: int = 512,
            overlap: int = 50,
            by_sentences: bool = False
    ) -> List[Dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text
            chunk_size: Maximum tokens per chunk
            overlap: Number of overlapping tokens
            by_sentences: If True, preserve sentence boundaries

        Returns:
            List of chunk dictionaries with metadata
        """
        doc = self.nlp(text)

        if by_sentences:
            chunks = self._chunk_by_sentences(doc, chunk_size, overlap)
        else:
            chunks = self._chunk_by_tokens(doc, chunk_size, overlap)

        logger.info(f"✓ Created {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
        return chunks

    def _chunk_by_tokens(
            self,
            doc,
            chunk_size: int,
            overlap: int
    ) -> List[Dict]:
        """Chunk by fixed token count"""
        tokens = [token.text for token in doc if not token.is_space]
        chunks = []

        start = 0
        chunk_id = 0

        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)

            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_token': start,
                'end_token': end,
                'num_tokens': len(chunk_tokens),
                'char_count': len(chunk_text)
            })

            chunk_id += 1
            start = end - overlap

        return chunks

    def _chunk_by_sentences(
            self,
            doc,
            chunk_size: int,
            overlap: int
    ) -> List[Dict]:
        """Chunk by preserving sentence boundaries"""
        chunks = []
        chunk_id = 0

        current_chunk = []
        current_size = 0

        for sent in doc.sents:
            sent_tokens = [token.text for token in sent if not token.is_space]
            sent_size = len(sent_tokens)

            if current_size + sent_size > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'num_tokens': current_size,
                    'char_count': len(chunk_text)
                })

                chunk_id += 1

                # Start new chunk with overlap
                overlap_tokens = current_chunk[-overlap:] if overlap < len(current_chunk) else current_chunk
                current_chunk = overlap_tokens + sent_tokens
                current_size = len(current_chunk)
            else:
                current_chunk.extend(sent_tokens)
                current_size += sent_size

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'num_tokens': current_size,
                'char_count': len(chunk_text)
            })

        return chunks

    def normalize_text(self, text: str, aggressive: bool = False) -> str:
        """
        Normalize text for consistency.

        Args:
            text: Input text
            aggressive: If True, perform more aggressive normalization

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        if aggressive:
            # Remove all special characters except periods and commas
            text = re.sub(r'[^a-zA-Z0-9\s\.,]', ' ', text)
        else:
            # Keep more punctuation
            text = re.sub(r'[^a-zA-Z0-9\s\.,!?;:\-]', ' ', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def preprocess_for_embeddings(self, text: str) -> str:
        """
        Preprocess text specifically for creating embeddings.

        Args:
            text: Input text

        Returns:
            Preprocessed text optimized for embeddings
        """
        # Light normalization (preserve semantic meaning)
        text = self.normalize_text(text, aggressive=False)

        # Don't remove stopwords (they provide context)
        # Don't lemmatize (can change meaning)

        return text

    def preprocess_for_search(self, text: str) -> str:
        """
        Preprocess text for search/keyword matching.

        Args:
            text: Input text

        Returns:
            Preprocessed text optimized for search
        """
        # Aggressive normalization
        text = self.normalize_text(text, aggressive=True)

        # Remove stopwords
        text = self.remove_stopwords(text)

        # Lemmatize
        text = self.lemmatize(text)

        return text

    def get_text_statistics(self, text: str) -> Dict:
        """
        Get statistics about the text.

        Args:
            text: Input text

        Returns:
            Dictionary with text statistics
        """
        doc = self.nlp(text)

        tokens = [token for token in doc if not token.is_space]
        words = [token for token in tokens if token.is_alpha]
        sentences = list(doc.sents)

        return {
            'total_characters': len(text),
            'total_tokens': len(tokens),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'avg_word_length': sum(len(token.text) for token in words) / max(len(words), 1),
            'avg_sentence_length': len(tokens) / max(len(sentences), 1)
        }


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TEXT PREPROCESSOR DEMONSTRATION")
    print("=" * 70)

    # Initialize preprocessor
    preprocessor = TextPreprocessor()

    # Sample text
    sample_text = """
    Deep learning has revolutionized natural language processing and computer vision.
    Convolutional Neural Networks (CNNs) are particularly effective for image classification tasks.
    Transformers, introduced in "Attention Is All You Need", have become the dominant architecture
    for NLP since 2017. Models like BERT and GPT have achieved remarkable performance on various benchmarks.
    """

    print("\nOriginal text:")
    print("-" * 70)
    print(sample_text.strip())

    # Tokenization
    print("\n1. Tokenization:")
    print("-" * 70)
    tokens = preprocessor.tokenize(sample_text)
    print(f"Tokens ({len(tokens)}): {tokens[:20]}...")

    # Chunking
    print("\n2. Text Chunking:")
    print("-" * 70)
    chunks = preprocessor.chunk_text(sample_text, chunk_size=20, overlap=5)
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  Chunk {chunk['chunk_id']}: {chunk['num_tokens']} tokens")
        print(f"    {chunk['text'][:80]}...")

    # Normalization
    print("\n3. Normalization:")
    print("-" * 70)
    normalized = preprocessor.normalize_text(sample_text)
    print(f"Normalized: {normalized[:200]}...")

    # Statistics
    print("\n4. Text Statistics:")
    print("-" * 70)
    stats = preprocessor.get_text_statistics(sample_text)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✓ PREPROCESSING COMPLETE")
    print("=" * 70)

