"""
PostgreSQL to Neo4j Data Sync Script
Syncs ERP data from PostgreSQL to Neo4j knowledge graph
"""
import psycopg2
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# PostgreSQL config
PG_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "erpagent"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password")
}

# Neo4j config
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def get_pg_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**PG_CONFIG)


def get_neo4j_driver():
    """Get Neo4j driver"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def sync_customers_to_neo4j(pg_conn, neo4j_session):
    """Sync customers from PostgreSQL to Neo4j"""
    logger.info("Syncing customers...")
    
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT customer_id, name, industry, credit_limit, status
            FROM customers
            LIMIT 100
        """)
        customers = cur.fetchall()
    
    count = 0
    for customer in customers:
        customer_id, name, industry, credit_limit, status = customer
        cypher = """
        MERGE (c:Customer {id: $id})
        SET c.name = $name,
            c.industry = $industry,
            c.credit_limit = $credit_limit,
            c.status = $status
        """
        neo4j_session.run(cypher, {
            "id": f"customer_{customer_id}",
            "name": name or "Unknown",
            "industry": industry or "Unknown",
            "credit_limit": float(credit_limit) if credit_limit else 0,
            "status": status or "active"
        })
        count += 1
    
    logger.info(f"  Synced {count} customers")
    return count


def sync_products_to_neo4j(pg_conn, neo4j_session):
    """Sync products from PostgreSQL to Neo4j"""
    logger.info("Syncing products...")
    
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT product_id, code, name, category, unit_price, stock, threshold
            FROM products
            LIMIT 100
        """)
        products = cur.fetchall()
    
    count = 0
    for product in products:
        product_id, code, name, category, unit_price, stock, threshold = product
        cypher = """
        MERGE (p:Product {id: $id})
        SET p.code = $code,
            p.name = $name,
            p.category = $category,
            p.unit_price = $unit_price,
            p.stock = $stock,
            p.threshold = $threshold
        """
        neo4j_session.run(cypher, {
            "id": f"product_{product_id}",
            "code": code or f"PROD-{product_id}",
            "name": name or "Unknown",
            "category": category or "General",
            "unit_price": float(unit_price) if unit_price else 0,
            "stock": int(stock) if stock else 0,
            "threshold": int(threshold) if threshold else 0
        })
        count += 1
    
    logger.info(f"  Synced {count} products")
    return count


def sync_orders_to_neo4j(pg_conn, neo4j_session):
    """Sync orders from PostgreSQL to Neo4j"""
    logger.info("Syncing orders...")
    
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT order_id, customer_id, order_date, total_amount, status
            FROM sales_orders
            LIMIT 100
        """)
        orders = cur.fetchall()
    
    count = 0
    for order in orders:
        order_id, customer_id, order_date, total_amount, status = order
        cypher = """
        MERGE (o:Order {id: $id})
        SET o.order_date = $order_date,
            o.total_amount = $total_amount,
            o.status = $status
        """
        neo4j_session.run(cypher, {
            "id": f"order_{order_id}",
            "order_date": str(order_date) if order_date else "",
            "total_amount": float(total_amount) if total_amount else 0,
            "status": status or "pending"
        })
        
        # Create relationship to customer
        if customer_id:
            rel_cypher = """
            MATCH (c:Customer {id: $customer_id})
            MATCH (o:Order {id: $order_id})
            MERGE (c)-[:PLACED]->(o)
            """
            neo4j_session.run(rel_cypher, {
                "customer_id": f"customer_{customer_id}",
                "order_id": f"order_{order_id}"
            })
        
        count += 1
    
    logger.info(f"  Synced {count} orders")
    return count


def sync_order_items_to_neo4j(pg_conn, neo4j_session):
    """Sync order items and create product relationships"""
    logger.info("Syncing order items...")
    
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT item_id, order_id, product_id, quantity, unit_price
            FROM order_items
            LIMIT 200
        """)
        items = cur.fetchall()
    
    count = 0
    for item in items:
        item_id, order_id, product_id, quantity, unit_price = item
        
        # Create CONTAINS relationship
        cypher = """
        MATCH (o:Order {id: $order_id})
        MATCH (p:Product {id: $product_id})
        MERGE (o)-[:CONTAINS {quantity: $quantity, unit_price: $unit_price}]->(p)
        """
        neo4j_session.run(cypher, {
            "order_id": f"order_{order_id}",
            "product_id": f"product_{product_id}",
            "quantity": int(quantity) if quantity else 0,
            "unit_price": float(unit_price) if unit_price else 0
        })
        count += 1
    
    logger.info(f"  Synced {count} order items")
    return count


def main():
    """Main sync function"""
    logger.info("=" * 60)
    logger.info("PostgreSQL to Neo4j Data Sync")
    logger.info("=" * 60)
    
    try:
        # Connect to databases
        logger.info(f"Connecting to PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
        pg_conn = get_pg_connection()
        logger.info("  [OK] PostgreSQL connected")
        
        logger.info(f"Connecting to Neo4j: {NEO4J_URI}")
        neo4j_driver = get_neo4j_driver()
        logger.info("  [OK] Neo4j connected")
        
        with neo4j_driver.session() as neo4j_session:
            # Clear existing data
            logger.info("Clearing existing Neo4j data...")
            neo4j_session.run("MATCH (n) DETACH DELETE n")
            logger.info("  [OK] Cleared")
            
            # Sync data
            total = 0
            total += sync_customers_to_neo4j(pg_conn, neo4j_session)
            total += sync_products_to_neo4j(pg_conn, neo4j_session)
            total += sync_orders_to_neo4j(pg_conn, neo4j_session)
            total += sync_order_items_to_neo4j(pg_conn, neo4j_session)
            
            # Get stats
            result = neo4j_session.run("MATCH (n) RETURN count(n) as nodes")
            node_count = result.single()["nodes"]
            
            result = neo4j_session.run("MATCH ()-[r]->() RETURN count(r) as rels")
            rel_count = result.single()["rels"]
            
            logger.info("=" * 60)
            logger.info(f"Sync Complete!")
            logger.info(f"  Total records: {total}")
            logger.info(f"  Neo4j nodes: {node_count}")
            logger.info(f"  Neo4j relationships: {rel_count}")
            logger.info("=" * 60)
        
        pg_conn.close()
        neo4j_driver.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
