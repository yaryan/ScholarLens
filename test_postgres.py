"""
Test PostgreSQL database connection
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()


def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("Testing PostgreSQL Connection...\n")

    try:
        # Create engine
        engine = create_engine(os.getenv('POSTGRES_URI'))

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]

            print("✓ PostgreSQL Connection Successful!")
            print(f"\nVersion: {version[:50]}...")

            # Test creating a simple table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    message VARCHAR(100)
                )
            """))
            conn.commit()

            print("✓ Table creation test successful!")

            # Clean up
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            conn.commit()

            print("✓ All PostgreSQL tests passed!\n")
            return True

    except Exception as e:
        print(f"✗ PostgreSQL Connection Failed: {e}")
        return False


if __name__ == "__main__":
    test_postgres_connection()
