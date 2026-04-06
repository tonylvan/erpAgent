"""
Neo4j Query Executor Service.

Provides Cypher query execution, result formatting, and error handling
for the ERP Agent knowledge graph system.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass

import neo4j
from neo4j import GraphDatabase, Driver, Session


class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


@dataclass
class QueryResult:
    """Container for query execution results."""
    data: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None
    query: Optional[str] = None


class QueryExecutor:
    """
    Neo4j Cypher query executor with connection management.
    
    Features:
    - Connection pooling via Neo4j driver
    - Synchronous and asynchronous query execution
    - Result formatting and transformation
    - Comprehensive error handling
    - Batch query support
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
        database: Optional[str] = None
    ):
        """
        Initialize QueryExecutor with Neo4j connection parameters.
        
        Args:
            uri: Neo4j bolt connection URI
            user: Database username
            password: Database password
            database: Optional database name (Neo4j 4.0+)
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver: Optional[Driver] = None
    
    def connect(self) -> None:
        """
        Establish connection to Neo4j database.
        
        Raises:
            QueryExecutionError: If connection fails
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            self.driver.verify_connectivity()
        except Exception as e:
            raise QueryExecutionError(
                f"Failed to connect to Neo4j at {self.uri}: {str(e)}",
                original_error=e
            )
    
    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query synchronously.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            database: Optional database name (overrides instance default)
            
        Returns:
            List of result records as dictionaries
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        if not self.driver:
            raise QueryExecutionError("Not connected to Neo4j. Call connect() first.")
        
        try:
            db_name = database or self.database
            with self.driver.session(database=db_name) as session:
                result = session.run(query, parameters or {})
                return list(result.data())
        except Exception as e:
            raise QueryExecutionError(
                f"Query execution failed: {str(e)}",
                original_error=e
            )
    
    async def execute_async(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query asynchronously.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            database: Optional database name (overrides instance default)
            
        Returns:
            List of result records as dictionaries
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        if not self.driver:
            raise QueryExecutionError("Not connected to Neo4j. Call connect() first.")
        
        try:
            db_name = database or self.database
            with self.driver.session(database=db_name) as session:
                # Run query in async context
                result = session.run(query, parameters or {})
                # Execute in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: list(result.data())
                )
                return data
        except Exception as e:
            raise QueryExecutionError(
                f"Async query execution failed: {str(e)}",
                original_error=e
            )
    
    def execute_batch(
        self,
        queries: List[Union[str, tuple]],
        database: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in a single session.
        
        Args:
            queries: List of query strings or (query, params) tuples
            database: Optional database name
            
        Returns:
            List of result lists, one per query
        """
        if not self.driver:
            raise QueryExecutionError("Not connected to Neo4j. Call connect() first.")
        
        results = []
        try:
            db_name = database or self.database
            with self.driver.session(database=db_name) as session:
                for query_item in queries:
                    if isinstance(query_item, tuple):
                        query, params = query_item
                    else:
                        query, params = query_item, None
                    
                    result = session.run(query, params)
                    results.append(list(result.data()))
                
                return results
        except Exception as e:
            raise QueryExecutionError(
                f"Batch query execution failed: {str(e)}",
                original_error=e
            )
    
    def format_result(
        self,
        data: List[Dict[str, Any]],
        single: bool = False,
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> Union[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Format query results with optional transformation.
        
        Args:
            data: Raw query result data
            single: If True, return first record or None
            transform: Optional function to transform each record
            
        Returns:
            Formatted result (single dict or list of dicts)
        """
        if single:
            if not data:
                return None
            record = data[0]
            if transform:
                return transform(record)
            return record
        
        if transform:
            data = [transform(record) for record in data]
        
        return data
    
    def execute_and_format(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        single: bool = False,
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> Union[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Execute query and format results in one call.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            single: If True, return first record or None
            transform: Optional function to transform each record
            
        Returns:
            Formatted result
        """
        data = self.execute(query, parameters)
        return self.format_result(data, single=single, transform=transform)
    
    def __enter__(self):
        """Context manager entry - establish connection."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
        return False  # Don't suppress exceptions
