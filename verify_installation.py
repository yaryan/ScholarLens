"""
Verification script to check all installations
"""
import sys


def check_imports():
    """Test importing all critical packages"""
    packages = [
        ('fastapi', 'FastAPI'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('neo4j', 'Neo4j Driver'),
        ('transformers', 'HuggingFace Transformers'),
        ('spacy', 'spaCy'),
        ('faiss', 'FAISS'),
        ('pdfplumber', 'pdfplumber'),
        ('PyPDF2', 'PyPDF2'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('arxiv', 'arXiv API'),
    ]

    print("Checking package imports...\n")
    all_success = True

    for package_name, display_name in packages:
        try:
            __import__(package_name)
            print(f"✓ {display_name:<30} OK")
        except ImportError as e:
            print(f"✗ {display_name:<30} FAILED: {e}")
            all_success = False

    # Check spaCy model
    print("\nChecking spaCy model...")
    try:
        import spacy
        nlp = spacy.load('en_core_web_md')
        print(f"✓ spaCy model 'en_core_web_md'     OK")
    except Exception as e:
        print(f"✗ spaCy model 'en_core_web_md'     FAILED: {e}")
        all_success = False

    print("\n" + "=" * 50)
    if all_success:
        print("✓ All packages installed successfully!")
    else:
        print("✗ Some packages failed to install. Check errors above.")
    print("=" * 50)

    return all_success


if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)
