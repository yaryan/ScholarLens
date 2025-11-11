"""
Test Neo4j database connection
"""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()


def test_neo4j_connection():
    """Test Neo4j connection"""
    print("Testing Neo4j Connection...\n")

    try:
        # Create driver
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )

        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 'Neo4j Connected!' AS message")
            record = result.single()

            print(f"✓ Neo4j Connection Successful!")
            print(f"\nMessage: {record['message']}")

            # Test creating and deleting a node
            session.run("""
                CREATE (n:TestNode {name: 'test'})
            """)
            print("✓ Node creation test successful!")

            # Clean up
            session.run("MATCH (n:TestNode) DELETE n")
            print("✓ All Neo4j tests passed!\n")

        driver.close()
        return True

    except Exception as e:
        print(f"✗ Neo4j Connection Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Neo4j container is running: docker ps")
        print("2. Check Neo4j Browser: http://localhost:7474")
        print("3. Verify credentials in .env file")
        return False


if __name__ == "__main__":
    test_neo4j_connection()
