"""
Neo4j Graph Database Schema and Manager

This module provides the Neo4j connection manager and graph operations
for building the research knowledge graph.
"""

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, ClientError
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jDatabase:
    """
    Neo4j database manager for knowledge graph operations.

    Optimized for 16GB RAM Windows system with memory-efficient queries.
    """

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Database username
            password: Database password
        """
        self.uri = uri or os.getenv('NEO4J_URI')
        self.user = user or os.getenv('NEO4J_USER')
        self.password = password or os.getenv('NEO4J_PASSWORD')

        if not all([self.uri, self.user, self.password]):
            raise ValueError("Neo4j credentials not found in environment variables")

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=50,
                connection_timeout=30,
                max_transaction_retry_time=30
            )

            # Test connection
            self.driver.verify_connectivity()
            logger.info("✓ Neo4j connection initialized")

        except ServiceUnavailable as e:
            logger.error(f"✗ Neo4j connection failed: {e}")
            logger.error("Make sure Docker container is running: docker ps")
            raise

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== SCHEMA INITIALIZATION ==========

    def create_constraints_and_indexes(self):
        """
        Create all constraints and indexes for optimal performance.

        Run this once when setting up the database.
        """
        constraints_and_indexes = [
            # Unique constraints for node IDs
            "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE",
            "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.author_id IS UNIQUE",
            "CREATE CONSTRAINT method_id_unique IF NOT EXISTS FOR (m:Method) REQUIRE m.method_id IS UNIQUE",
            "CREATE CONSTRAINT dataset_id_unique IF NOT EXISTS FOR (d:Dataset) REQUIRE d.dataset_id IS UNIQUE",
            "CREATE CONSTRAINT institution_id_unique IF NOT EXISTS FOR (i:Institution) REQUIRE i.institution_id IS UNIQUE",

            # Indexes for common queries
            "CREATE INDEX paper_title_idx IF NOT EXISTS FOR (p:Paper) ON (p.title)",
            "CREATE INDEX paper_date_idx IF NOT EXISTS FOR (p:Paper) ON (p.published_date)",
            "CREATE INDEX paper_category_idx IF NOT EXISTS FOR (p:Paper) ON (p.primary_category)",
            "CREATE INDEX author_name_idx IF NOT EXISTS FOR (a:Author) ON (a.name)",
            "CREATE INDEX method_name_idx IF NOT EXISTS FOR (m:Method) ON (m.name)",
            "CREATE INDEX method_category_idx IF NOT EXISTS FOR (m:Method) ON (m.category)",
            "CREATE INDEX dataset_name_idx IF NOT EXISTS FOR (d:Dataset) ON (d.name)",
            "CREATE INDEX institution_name_idx IF NOT EXISTS FOR (i:Institution) ON (i.name)",

            # Full-text indexes for search
            "CREATE FULLTEXT INDEX paper_search_idx IF NOT EXISTS FOR (p:Paper) ON EACH [p.title, p.abstract]",
            "CREATE FULLTEXT INDEX author_search_idx IF NOT EXISTS FOR (a:Author) ON EACH [a.name]"
        ]

        with self.driver.session() as session:
            for constraint in constraints_and_indexes:
                try:
                    session.run(constraint)
                    logger.info(f"✓ Created: {constraint.split()[1]}")
                except ClientError as e:
                    if "equivalent" in str(e).lower():
                        logger.info(f"⚠ Already exists: {constraint.split()[1]}")
                    else:
                        logger.warning(f"⚠ Could not create: {e}")

        logger.info("✓ All constraints and indexes processed")

    # ========== NODE CREATION OPERATIONS ==========

    def create_paper_node(self, paper_id: int, title: str, abstract: str = None,
                          published_date: str = None, categories: List[str] = None,
                          arxiv_id: str = None) -> Dict:
        """
        Create or update a Paper node.

        Args:
            paper_id: Unique paper identifier
            title: Paper title
            abstract: Paper abstract
            published_date: Publication date (YYYY-MM-DD)
            categories: List of categories
            arxiv_id: arXiv identifier

        Returns:
            Created node properties
        """
        query = """
        MERGE (p:Paper {paper_id: $paper_id})
        SET p.title = $title,
            p.abstract = $abstract,
            p.published_date = date($published_date),
            p.categories = $categories,
            p.arxiv_id = $arxiv_id,
            p.updated_at = datetime()
        RETURN p
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                paper_id=paper_id,
                title=title,
                abstract=abstract,
                published_date=published_date,
                categories=categories or [],
                arxiv_id=arxiv_id
            )

            node = result.single()
            logger.info(f"✓ Created/Updated Paper node: {paper_id}")
            return dict(node['p']) if node else {}

    def create_author_node(self, author_id: int, name: str, email: str = None,
                           orcid: str = None) -> Dict:
        """
        Create or update an Author node.

        Args:
            author_id: Unique author identifier
            name: Author name
            email: Author email
            orcid: ORCID identifier

        Returns:
            Created node properties
        """
        query = """
        MERGE (a:Author {author_id: $author_id})
        SET a.name = $name,
            a.email = $email,
            a.orcid = $orcid,
            a.updated_at = datetime()
        RETURN a
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                author_id=author_id,
                name=name,
                email=email,
                orcid=orcid
            )

            node = result.single()
            logger.info(f"✓ Created/Updated Author node: {name}")
            return dict(node['a']) if node else {}

    def create_method_node(self, method_id: int, name: str, description: str = None,
                           category: str = None) -> Dict:
        """
        Create or update a Method node.

        Args:
            method_id: Unique method identifier
            name: Method name
            description: Method description
            category: Method category

        Returns:
            Created node properties
        """
        query = """
        MERGE (m:Method {method_id: $method_id})
        SET m.name = $name,
            m.description = $description,
            m.category = $category,
            m.updated_at = datetime()
        RETURN m
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                method_id=method_id,
                name=name,
                description=description,
                category=category
            )

            node = result.single()
            logger.info(f"✓ Created/Updated Method node: {name}")
            return dict(node['m']) if node else {}

    def create_dataset_node(self, dataset_id: int, name: str, domain: str = None,
                            description: str = None) -> Dict:
        """
        Create or update a Dataset node.

        Args:
            dataset_id: Unique dataset identifier
            name: Dataset name
            domain: Dataset domain
            description: Dataset description

        Returns:
            Created node properties
        """
        query = """
        MERGE (d:Dataset {dataset_id: $dataset_id})
        SET d.name = $name,
            d.domain = $domain,
            d.description = $description,
            d.updated_at = datetime()
        RETURN d
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                dataset_id=dataset_id,
                name=name,
                domain=domain,
                description=description
            )

            node = result.single()
            logger.info(f"✓ Created/Updated Dataset node: {name}")
            return dict(node['d']) if node else {}

    def create_institution_node(self, institution_id: int, name: str,
                                country: str = None, city: str = None) -> Dict:
        """
        Create or update an Institution node.

        Args:
            institution_id: Unique institution identifier
            name: Institution name
            country: Country
            city: City

        Returns:
            Created node properties
        """
        query = """
        MERGE (i:Institution {institution_id: $institution_id})
        SET i.name = $name,
            i.country = $country,
            i.city = $city,
            i.updated_at = datetime()
        RETURN i
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                institution_id=institution_id,
                name=name,
                country=country,
                city=city
            )

            node = result.single()
            logger.info(f"✓ Created/Updated Institution node: {name}")
            return dict(node['i']) if node else {}

    # ========== RELATIONSHIP CREATION OPERATIONS ==========

    def create_authored_relationship(self, paper_id: int, author_id: int,
                                     position: int = None) -> bool:
        """
        Create AUTHORED relationship: (Author)-[:AUTHORED]->(Paper)

        Args:
            paper_id: Paper ID
            author_id: Author ID
            position: Author position in author list

        Returns:
            True if successful
        """
        query = """
        MATCH (a:Author {author_id: $author_id})
        MATCH (p:Paper {paper_id: $paper_id})
        MERGE (a)-[r:AUTHORED]->(p)
        SET r.position = $position,
            r.created_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                paper_id=paper_id,
                author_id=author_id,
                position=position
            )

            success = result.single() is not None
            if success:
                logger.info(f"✓ Created AUTHORED: Author {author_id} -> Paper {paper_id}")
            return success

    def create_uses_method_relationship(self, paper_id: int, method_id: int,
                                        context: str = None) -> bool:
        """
        Create USES_METHOD relationship: (Paper)-[:USES_METHOD]->(Method)

        Args:
            paper_id: Paper ID
            method_id: Method ID
            context: Context where method is used

        Returns:
            True if successful
        """
        query = """
        MATCH (p:Paper {paper_id: $paper_id})
        MATCH (m:Method {method_id: $method_id})
        MERGE (p)-[r:USES_METHOD]->(m)
        SET r.context = $context,
            r.created_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                paper_id=paper_id,
                method_id=method_id,
                context=context
            )

            success = result.single() is not None
            if success:
                logger.info(f"✓ Created USES_METHOD: Paper {paper_id} -> Method {method_id}")
            return success

    def create_uses_dataset_relationship(self, paper_id: int, dataset_id: int,
                                         usage_type: str = None) -> bool:
        """
        Create USES_DATASET relationship: (Paper)-[:USES_DATASET]->(Dataset)

        Args:
            paper_id: Paper ID
            dataset_id: Dataset ID
            usage_type: How dataset is used (training, testing, etc.)

        Returns:
            True if successful
        """
        query = """
        MATCH (p:Paper {paper_id: $paper_id})
        MATCH (d:Dataset {dataset_id: $dataset_id})
        MERGE (p)-[r:USES_DATASET]->(d)
        SET r.usage_type = $usage_type,
            r.created_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                paper_id=paper_id,
                dataset_id=dataset_id,
                usage_type=usage_type
            )

            success = result.single() is not None
            if success:
                logger.info(f"✓ Created USES_DATASET: Paper {paper_id} -> Dataset {dataset_id}")
            return success

    def create_cites_relationship(self, citing_paper_id: int, cited_paper_id: int,
                                  context: str = None) -> bool:
        """
        Create CITES relationship: (Paper)-[:CITES]->(Paper)

        Args:
            citing_paper_id: ID of paper that cites
            cited_paper_id: ID of paper being cited
            context: Citation context

        Returns:
            True if successful
        """
        query = """
        MATCH (p1:Paper {paper_id: $citing_paper_id})
        MATCH (p2:Paper {paper_id: $cited_paper_id})
        MERGE (p1)-[r:CITES]->(p2)
        SET r.context = $context,
            r.created_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                citing_paper_id=citing_paper_id,
                cited_paper_id=cited_paper_id,
                context=context
            )

            success = result.single() is not None
            if success:
                logger.info(f"✓ Created CITES: Paper {citing_paper_id} -> Paper {cited_paper_id}")
            return success

    def create_collaborates_relationship(self, author1_id: int, author2_id: int,
                                         paper_id: int) -> bool:
        """
        Create COLLABORATES relationship: (Author)-[:COLLABORATES]-(Author)

        This creates an undirected relationship and tracks shared papers.

        Args:
            author1_id: First author ID
            author2_id: Second author ID
            paper_id: Paper they collaborated on

        Returns:
            True if successful
        """
        query = """
        MATCH (a1:Author {author_id: $author1_id})
        MATCH (a2:Author {author_id: $author2_id})
        MERGE (a1)-[r:COLLABORATES]-(a2)
        ON CREATE SET r.paper_count = 1, r.papers = [$paper_id], r.first_collaboration = datetime()
        ON MATCH SET r.paper_count = r.paper_count + 1, 
                     r.papers = r.papers + $paper_id,
                     r.last_collaboration = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                author1_id=author1_id,
                author2_id=author2_id,
                paper_id=paper_id
            )

            success = result.single() is not None
            if success:
                logger.info(f"✓ Created/Updated COLLABORATES: Author {author1_id} <-> Author {author2_id}")
            return success

    def create_affiliated_with_relationship(self, author_id: int, institution_id: int,
                                            position: str = None) -> bool:
        """
        Create AFFILIATED_WITH relationship: (Author)-[:AFFILIATED_WITH]->(Institution)

        Args:
            author_id: Author ID
            institution_id: Institution ID
            position: Position at institution

        Returns:
            True if successful
        """
        query = """
        MATCH (a:Author {author_id: $author_id})
        MATCH (i:Institution {institution_id: $institution_id})
        MERGE (a)-[r:AFFILIATED_WITH]->(i)
        SET r.position = $position,
            r.created_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                author_id=author_id,
                institution_id=institution_id,
                position=position
            )

            success = result.single() is not None
            if success:
                logger.info(f"✓ Created AFFILIATED_WITH: Author {author_id} -> Institution {institution_id}")
            return success

    # ========== QUERY OPERATIONS ==========

    def get_paper_by_id(self, paper_id: int) -> Optional[Dict]:
        """Get paper node by ID"""
        query = "MATCH (p:Paper {paper_id: $paper_id}) RETURN p"

        with self.driver.session() as session:
            result = session.run(query, paper_id=paper_id)
            record = result.single()
            return dict(record['p']) if record else None

    def get_author_papers(self, author_id: int) -> List[Dict]:
        """Get all papers authored by a specific author"""
        query = """
        MATCH (a:Author {author_id: $author_id})-[:AUTHORED]->(p:Paper)
        RETURN p
        ORDER BY p.published_date DESC
        """

        with self.driver.session() as session:
            result = session.run(query, author_id=author_id)
            return [dict(record['p']) for record in result]

    def get_paper_citations(self, paper_id: int) -> Dict[str, List]:
        """
        Get papers that cite this paper and papers cited by this paper.

        Returns:
            Dictionary with 'citing_papers' and 'cited_papers' lists
        """
        query = """
        MATCH (p:Paper {paper_id: $paper_id})
        OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
        OPTIONAL MATCH (p)-[:CITES]->(cited:Paper)
        RETURN collect(DISTINCT citing) as citing_papers,
               collect(DISTINCT cited) as cited_papers
        """

        with self.driver.session() as session:
            result = session.run(query, paper_id=paper_id)
            record = result.single()

            return {
                'citing_papers': [dict(p) for p in record['citing_papers'] if p],
                'cited_papers': [dict(p) for p in record['cited_papers'] if p]
            }

    def get_author_collaborators(self, author_id: int, min_papers: int = 1) -> List[Dict]:
        """
        Get authors who have collaborated with this author.

        Args:
            author_id: Author ID
            min_papers: Minimum number of shared papers

        Returns:
            List of collaborator dictionaries
        """
        query = """
        MATCH (a:Author {author_id: $author_id})-[r:COLLABORATES]-(collaborator:Author)
        WHERE r.paper_count >= $min_papers
        RETURN collaborator, r.paper_count as shared_papers
        ORDER BY shared_papers DESC
        """

        with self.driver.session() as session:
            result = session.run(query, author_id=author_id, min_papers=min_papers)
            return [
                {
                    'author': dict(record['collaborator']),
                    'shared_papers': record['shared_papers']
                }
                for record in result
            ]

    def get_papers_by_method(self, method_id: int) -> List[Dict]:
        """Get all papers that use a specific method"""
        query = """
        MATCH (p:Paper)-[:USES_METHOD]->(m:Method {method_id: $method_id})
        RETURN p
        ORDER BY p.published_date DESC
        """

        with self.driver.session() as session:
            result = session.run(query, method_id=method_id)
            return [dict(record['p']) for record in result]

    def search_papers_fulltext(self, search_text: str, limit: int = 10) -> List[Dict]:
        """
        Full-text search in papers.

        Args:
            search_text: Search query
            limit: Maximum results

        Returns:
            List of matching papers
        """
        query = """
        CALL db.index.fulltext.queryNodes('paper_search_idx', $search_text)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, search_text=search_text, limit=limit)
            return [
                {
                    'paper': dict(record['node']),
                    'score': record['score']
                }
                for record in result
            ]

    # ========== ANALYTICS OPERATIONS ==========

    def get_graph_statistics(self) -> Dict:
        """Get overall graph statistics with better error handling"""
        with self.driver.session() as session:
            stats = {}

            # Count nodes separately
            try:
                result = session.run("MATCH (p:Paper) RETURN count(p) as count")
                stats['papers'] = result.single()['count']
            except:
                stats['papers'] = 0

            try:
                result = session.run("MATCH (a:Author) RETURN count(a) as count")
                stats['authors'] = result.single()['count']
            except:
                stats['authors'] = 0

            try:
                result = session.run("MATCH (m:Method) RETURN count(m) as count")
                stats['methods'] = result.single()['count']
            except:
                stats['methods'] = 0

            try:
                result = session.run("MATCH (d:Dataset) RETURN count(d) as count")
                stats['datasets'] = result.single()['count']
            except:
                stats['datasets'] = 0

            try:
                result = session.run("MATCH (i:Institution) RETURN count(i) as count")
                stats['institutions'] = result.single()['count']
            except:
                stats['institutions'] = 0

            # Count relationships separately
            try:
                result = session.run("MATCH ()-[r:CITES]->() RETURN count(r) as count")
                stats['citations'] = result.single()['count']
            except:
                stats['citations'] = 0

            try:
                result = session.run("MATCH ()-[r:COLLABORATES]-() RETURN count(r)/2 as count")
                stats['collaborations'] = int(result.single()['count'])
            except:
                stats['collaborations'] = 0

            return stats

    def get_most_cited_papers(self, limit: int = 10) -> List[Dict]:
        """Get most cited papers"""
        query = """
        MATCH (p:Paper)
        OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
        WITH p, count(citing) as citation_count
        WHERE citation_count > 0
        RETURN p, citation_count
        ORDER BY citation_count DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [
                {
                    'paper': dict(record['p']),
                    'citation_count': record['citation_count']
                }
                for record in result
            ]

    def get_top_authors_by_paper_count(self, limit: int = 10) -> List[Dict]:
        """Get authors with most papers"""
        query = """
        MATCH (a:Author)-[:AUTHORED]->(p:Paper)
        WITH a, count(p) as paper_count
        RETURN a, paper_count
        ORDER BY paper_count DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [
                {
                    'author': dict(record['a']),
                    'paper_count': record['paper_count']
                }
                for record in result
            ]

    # ========== BATCH OPERATIONS ==========

    def batch_create_papers(self, papers_data: List[Dict]) -> int:
        """
        Batch create multiple paper nodes efficiently.

        Args:
            papers_data: List of paper dictionaries

        Returns:
            Number of papers created
        """
        query = """
        UNWIND $papers as paper_data
        MERGE (p:Paper {paper_id: paper_data.paper_id})
        SET p.title = paper_data.title,
            p.abstract = paper_data.abstract,
            p.published_date = date(paper_data.published_date),
            p.categories = paper_data.categories,
            p.arxiv_id = paper_data.arxiv_id,
            p.updated_at = datetime()
        RETURN count(p) as created_count
        """

        with self.driver.session() as session:
            result = session.run(query, papers=papers_data)
            count = result.single()['created_count']
            logger.info(f"✓ Batch created {count} papers")
            return count

    def execute_custom_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a custom Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]


# Example usage
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("NEO4J DATABASE DEMONSTRATION")
    print("=" * 70)

    # Initialize database
    neo4j_db = Neo4jDatabase()

    try:
        # Create constraints and indexes
        print("\nCreating constraints and indexes...")
        neo4j_db.create_constraints_and_indexes()

        # Get statistics
        print("\nGraph Statistics:")
        print("-" * 70)
        stats = neo4j_db.get_graph_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Test creating nodes
        print("\nTesting node creation...")
        print("-" * 70)

        # Create a paper
        paper = neo4j_db.create_paper_node(
            paper_id=1,
            title="Attention Is All You Need",
            abstract="The dominant sequence transduction models...",
            published_date="2017-06-12",
            categories=["cs.CL", "cs.LG"],
            arxiv_id="1706.03762"
        )
        print(f"Created paper: {paper.get('title', 'Unknown')}")

        # Create an author
        author = neo4j_db.create_author_node(
            author_id=1,
            name="Ashish Vaswani",
            email="vaswani@google.com"
        )
        print(f"Created author: {author.get('name', 'Unknown')}")

        # Create relationship
        neo4j_db.create_authored_relationship(paper_id=1, author_id=1, position=1)

        print("\n" + "=" * 70)
        print("✓ NEO4J DEMONSTRATION COMPLETE")
        print("=" * 70)

    finally:
        neo4j_db.close()
