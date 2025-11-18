"""
Entity Extraction Pipeline for Research Papers

This module extracts named entities from research papers including:
- Authors (via spaCy NER)
- Methods/Techniques (via patterns and NER)
- Datasets (via patterns)
- Institutions (via NER and keywords)

Optimized for 16GB RAM Windows system.
"""

import spacy
from spacy.tokens import Span
from typing import List, Dict, Set, Tuple
import re
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extract named entities from research papers.

    Features:
    - spaCy-based NER for persons and organizations
    - Pattern matching for methods and datasets
    - Configurable patterns via JSON
    - Batch processing for memory efficiency
    """

    def __init__(self, model_name: str = 'en_core_web_md',
                 patterns_path: str = 'config/entity_patterns.json'):
        """
        Initialize entity extractor.

        Args:
            model_name: spaCy model to use
            patterns_path: Path to entity patterns JSON
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"✓ Loaded spaCy model: {model_name}")
        except OSError:
            logger.error(f"✗ Model '{model_name}' not found. Run: python -m spacy download {model_name}")
            raise

        # Load patterns
        self.patterns = self._load_patterns(patterns_path)

        # Compile regex patterns for efficiency
        self.method_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.patterns['methods']['patterns']
        ]

        self.dataset_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.patterns['datasets']['patterns']
        ]

        self.institution_keywords = self.patterns['institutions']['keywords']

        logger.info("✓ Entity extractor initialized")

    def _load_patterns(self, patterns_path: str) -> Dict:
        """Load entity patterns from JSON file"""
        path = Path(patterns_path)

        if not path.exists():
            logger.warning(f"Patterns file not found: {patterns_path}")
            return self._get_default_patterns()

        try:
            with open(path, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            logger.info(f"✓ Loaded patterns from {patterns_path}")
            return patterns
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict:
        """Return default patterns if file not found"""
        return {
            'methods': {
                'patterns': [
                    r'\b(?:CNN|RNN|LSTM|GRU|BERT|GPT)\b',
                    r'\btransformer[s]?\b'
                ],
                'known_methods': ['CNN', 'RNN', 'LSTM', 'Transformer']
            },
            'datasets': {
                'patterns': [
                    r'\b(?:ImageNet|MNIST|CIFAR)\b'
                ],
                'known_datasets': ['ImageNet', 'MNIST', 'CIFAR']
            },
            'institutions': {
                'keywords': ['University', 'Institute', 'College']
            }
        }

    def extract_entities(self, text: str, paper_id: int = None) -> Dict[str, List[Dict]]:
        """
        Extract all entity types from text.

        Args:
            text: Input text
            paper_id: Optional paper ID for context

        Returns:
            Dictionary with entity types as keys
        """
        # Process with spaCy
        doc = self.nlp(text[:1000000])  # Limit text length for memory

        entities = {
            'persons': [],
            'organizations': [],
            'institutions': [],
            'methods': [],
            'datasets': [],
            'locations': []
        }

        # Extract standard NER entities
        for ent in doc.ents:
            entity_dict = {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            }

            if ent.label_ == 'PERSON':
                entities['persons'].append(entity_dict)
            elif ent.label_ == 'ORG':
                # Check if it's an institution
                if self._is_institution(ent.text):
                    entity_dict['type'] = 'institution'
                    entities['institutions'].append(entity_dict)
                else:
                    entities['organizations'].append(entity_dict)
            elif ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(entity_dict)

        # Extract methods using patterns
        entities['methods'] = self._extract_methods(text)

        # Extract datasets using patterns
        entities['datasets'] = self._extract_datasets(text)

        # Remove duplicates
        for key in entities:
            entities[key] = self._remove_duplicates(entities[key])

        # Add paper_id if provided
        if paper_id:
            for entity_type in entities:
                for entity in entities[entity_type]:
                    entity['paper_id'] = paper_id

        logger.debug(f"Extracted entities: {sum(len(v) for v in entities.values())} total")
        return entities

    def _is_institution(self, org_name: str) -> bool:
        """Check if organization name matches institution keywords"""
        return any(keyword.lower() in org_name.lower()
                   for keyword in self.institution_keywords)

    def _extract_methods(self, text: str) -> List[Dict]:
        """Extract methods/techniques using regex patterns"""
        methods = []
        seen = set()

        for pattern in self.method_patterns:
            for match in pattern.finditer(text):
                method_text = match.group().strip()

                # Normalize method name
                normalized = self._normalize_method_name(method_text)

                if normalized not in seen:
                    seen.add(normalized)
                    methods.append({
                        'text': method_text,
                        'normalized': normalized,
                        'start': match.start(),
                        'end': match.end()
                    })

        return methods

    def _normalize_method_name(self, method_text: str) -> str:
        """Normalize method names for deduplication"""
        # Convert to title case and remove extra spaces
        normalized = ' '.join(method_text.split()).title()

        # Handle acronyms (keep uppercase)
        if method_text.isupper() and len(method_text) <= 5:
            normalized = method_text.upper()

        return normalized

    def _extract_datasets(self, text: str) -> List[Dict]:
        """Extract dataset names using regex patterns"""
        datasets = []
        seen = set()

        for pattern in self.dataset_patterns:
            for match in pattern.finditer(text):
                dataset_text = match.group().strip()
                normalized = dataset_text.upper()

                if normalized not in seen:
                    seen.add(normalized)
                    datasets.append({
                        'text': dataset_text,
                        'normalized': normalized,
                        'start': match.start(),
                        'end': match.end()
                    })

        return datasets

    def _remove_duplicates(self, entity_list: List[Dict]) -> List[Dict]:
        """Remove duplicate entities based on normalized text"""
        seen = set()
        unique = []

        for entity in entity_list:
            # Use normalized text if available, otherwise lowercase text
            key = entity.get('normalized', entity['text'].lower())

            if key not in seen:
                seen.add(key)
                unique.append(entity)

        return unique

    def extract_author_names(self, text: str) -> List[str]:
        """
        Extract author names from text.
        Useful for parsing author sections.

        Args:
            text: Text containing author names

        Returns:
            List of author names
        """
        doc = self.nlp(text)
        authors = []

        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                authors.append(ent.text)

        return self._remove_duplicate_strings(authors)

    def _remove_duplicate_strings(self, str_list: List[str]) -> List[str]:
        """Remove duplicate strings while preserving order"""
        seen = set()
        unique = []

        for s in str_list:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)

        return unique

    def batch_extract(self, texts: List[str], batch_size: int = 10) -> List[Dict]:
        """
        Extract entities from multiple texts efficiently.
        Memory-optimized for 16GB RAM.

        Args:
            texts: List of text strings
            batch_size: Process texts in batches

        Returns:
            List of entity dictionaries
        """
        all_entities = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                entities = self.extract_entities(text)
                all_entities.append(entities)

            logger.info(f"Processed batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")

        return all_entities

    def get_statistics(self, entities: Dict[str, List[Dict]]) -> Dict:
        """Get statistics about extracted entities"""
        stats = {}

        for entity_type, entity_list in entities.items():
            stats[entity_type] = {
                'count': len(entity_list),
                'unique': len(set(e.get('normalized', e['text'].lower())
                                  for e in entity_list))
            }

        stats['total'] = sum(s['count'] for s in stats.values())

        return stats


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ENTITY EXTRACTION DEMONSTRATION")
    print("=" * 70)

    # Initialize extractor
    extractor = EntityExtractor()

    # Sample research paper abstract
    sample_text = """
    This paper introduces a novel Convolutional Neural Network (CNN) architecture 
    for image classification. We evaluate our model on ImageNet and CIFAR-10 datasets,
    achieving state-of-the-art performance. The authors, John Smith from Stanford University
    and Jane Doe from MIT, propose a new attention mechanism that improves upon previous
    Transformer-based approaches. Our method uses BERT embeddings and achieves 95% accuracy
    on the SQuAD benchmark. We also compare our results with ResNet and VGG architectures.
    """

    # Extract entities
    print("\nSample Text:")
    print("-" * 70)
    print(sample_text.strip())

    print("\n\nExtracted Entities:")
    print("-" * 70)

    entities = extractor.extract_entities(sample_text)

    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"\n{entity_type.upper()}:")
            for entity in entity_list:
                print(f"  - {entity['text']}")

    # Statistics
    print("\n\nStatistics:")
    print("-" * 70)
    stats = extractor.get_statistics(entities)

    for entity_type, stat in stats.items():
        if entity_type != 'total':
            print(f"{entity_type}: {stat['count']} total, {stat['unique']} unique")

    print(f"\nTotal entities: {stats['total']}")

    print("\n" + "=" * 70)
    print("✓ ENTITY EXTRACTION COMPLETE")
    print("=" * 70)
