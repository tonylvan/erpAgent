#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j Password Reset Script using Cypher commands
This script connects to Neo4j and changes the password
"""

import sys
import argparse

def reset_password(old_password, new_password, uri="bolt://localhost:7687", username="neo4j"):
    """Reset Neo4j password using Cypher command"""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("ERROR: neo4j-python-driver not installed")
        print("Install with: pip install neo4j")
        return False
    
    try:
        # Connect with old password
        print(f"Connecting to {uri}...")
        driver = GraphDatabase.driver(uri, auth=(username, old_password))
        
        # Verify connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("[OK] Connection successful")
        
        # Change password
        print(f"Changing password for user '{username}'...")
        with driver.session() as session:
            # Use ALTER USER to change password
            cypher = f'ALTER USER {username} SET PASSWORD "{new_password}"'
            session.run(cypher)
        
        driver.close()
        
        print("[OK] Password changed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Reset Neo4j password')
    parser.add_argument('--old-password', default='neo4j', help='Current password (default: neo4j)')
    parser.add_argument('--new-password', default='Tony1985', help='New password (default: Tony1985)')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--username', default='neo4j', help='Neo4j username')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("  Neo4j Password Reset Tool")
    print("=" * 50)
    print()
    
    success = reset_password(
        old_password=args.old_password,
        new_password=args.new_password,
        uri=args.uri,
        username=args.username
    )
    
    if success:
        print()
        print("=" * 50)
        print("  Password Reset Complete!")
        print("=" * 50)
        print()
        print("New Credentials:")
        print(f"  Username: {args.username}")
        print(f"  Password: {args.new_password}")
        print()
        print("Connection Details:")
        print(f"  URI: {args.uri}")
        print()
        return 0
    else:
        print()
        print("Password reset failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
