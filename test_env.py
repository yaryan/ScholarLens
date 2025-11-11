"""
Test environment variable loading
"""
from dotenv import load_dotenv
import os

load_dotenv()

print("Testing Environment Variables:\n")
print(f"POSTGRES_URI: {os.getenv('POSTGRES_URI')}")
print(f"NEO4J_URI: {os.getenv('NEO4J_URI')}")
print(f"NEO4J_USER: {os.getenv('NEO4J_USER')}")
print(f"NEO4J_PASSWORD: {'*' * len(os.getenv('NEO4J_PASSWORD', ''))}")
print(f"EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL')}")
print(f"VECTOR_DIMENSION: {os.getenv('VECTOR_DIMENSION')}")
print(f"\n✓ Environment variables loaded successfully!")
