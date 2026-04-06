"""
Test suite for QueryExecutor service.
Tests Neo4j Cypher query execution and result handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from app.services.query_executor import QueryExecutor, QueryExecutionError


class TestQueryExecutorInit:
    """Test QueryExecutor initialization and connection management."""

    def test_init_with_default_uri(self):
        """Test initialization with default Neo4j URI."""
        executor = QueryExecutor()
        assert executor.uri == "bolt://localhost:7687"
        assert executor.driver is None

    def test_init_with_custom_credentials(self):
        """Test initialization with custom credentials."""
        executor = QueryExecutor(
            uri="bolt://custom:7687",
            user="test_user",
            password="test_pass"
        )
        assert executor.uri == "bolt://custom:7687"
        assert executor.user == "test_user"
        assert executor.password == "test_pass"


class TestQueryExecutorConnection:
    """Test connection management."""

    @patch('app.services.query_executor.GraphDatabase')
    def test_connect_success(self, mock_graph_db):
        """Test successful connection to Neo4j."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        # Mock verify_connectivity to avoid actual connection
        mock_driver.verify_connectivity = Mock()
        
        executor = QueryExecutor()
        executor.connect()
        
        assert executor.driver == mock_driver
        mock_graph_db.driver.assert_called_once()
        mock_driver.verify_connectivity.assert_called_once()

    @patch('app.services.query_executor.neo4j')
    def test_connect_failure(self, mock_neo4j):
        """Test connection failure handling."""
        mock_neo4j.GraphDatabase.driver.side_effect = Exception("Connection failed")
        
        executor = QueryExecutor()
        with pytest.raises(QueryExecutionError) as exc_info:
            executor.connect()
        
        assert "Failed to connect" in str(exc_info.value)

    def test_close_connection(self):
        """Test closing connection."""
        mock_driver = Mock()
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        executor.close()
        
        mock_driver.close.assert_called_once()
        assert executor.driver is None


class TestQueryExecutorExecute:
    """Test query execution functionality."""

    @patch('app.services.query_executor.neo4j')
    def test_execute_read_query(self, mock_neo4j):
        """Test executing a read query."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_result.data.return_value = [{"name": "Test", "id": 1}]
        
        mock_neo4j.GraphDatabase.driver.return_value = mock_driver
        
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        result = executor.execute("MATCH (n) RETURN n.name, n.id")
        
        assert result == [{"name": "Test", "id": 1}]
        mock_session.run.assert_called_once()

    @patch('app.services.query_executor.neo4j')
    def test_execute_write_query(self, mock_neo4j):
        """Test executing a write query with parameters."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_result.consume.return_value = Mock()
        mock_result.data.return_value = [{"created": True}]
        
        mock_neo4j.GraphDatabase.driver.return_value = mock_driver
        
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        params = {"name": "TestNode", "value": 100}
        result = executor.execute(
            "CREATE (n:Test {name: $name, value: $value}) RETURN true as created",
            params
        )
        
        assert result == [{"created": True}]
        mock_session.run.assert_called_once()

    @patch('app.services.query_executor.neo4j')
    def test_execute_query_error(self, mock_neo4j):
        """Test query execution error handling."""
        mock_driver = Mock()
        mock_session = Mock()
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.side_effect = Exception("Cypher syntax error")
        
        mock_neo4j.GraphDatabase.driver.return_value = mock_driver
        
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        with pytest.raises(QueryExecutionError) as exc_info:
            executor.execute("INVALID CYPHER QUERY")
        
        assert "Query execution failed" in str(exc_info.value)


class TestQueryExecutorAsync:
    """Test asynchronous query execution."""

    @patch('app.services.query_executor.neo4j')
    @pytest.mark.asyncio
    async def test_execute_async(self, mock_neo4j):
        """Test asynchronous query execution."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_result.data.return_value = [{"async_result": True}]
        
        mock_neo4j.GraphDatabase.driver.return_value = mock_driver
        
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        result = await executor.execute_async("MATCH (n) RETURN n LIMIT 1")
        
        assert result == [{"async_result": True}]

    @patch('app.services.query_executor.neo4j')
    @pytest.mark.asyncio
    async def test_execute_async_with_params(self, mock_neo4j):
        """Test asynchronous query execution with parameters."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_result.data.return_value = [{"count": 5}]
        
        mock_neo4j.GraphDatabase.driver.return_value = mock_driver
        
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        params = {"label": "User"}
        result = await executor.execute_async(
            "MATCH (n:$label) RETURN count(n) as count",
            params
        )
        
        assert result == [{"count": 5}]


class TestQueryExecutorFormatting:
    """Test result formatting functionality."""

    def test_format_single_record(self):
        """Test formatting single record result."""
        executor = QueryExecutor()
        data = [{"name": "John", "age": 30}]
        
        result = executor.format_result(data, single=True)
        
        assert result == {"name": "John", "age": 30}

    def test_format_single_record_empty(self):
        """Test formatting empty result as single."""
        executor = QueryExecutor()
        data = []
        
        result = executor.format_result(data, single=True)
        
        assert result is None

    def test_format_list_result(self):
        """Test formatting list result."""
        executor = QueryExecutor()
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        result = executor.format_result(data, single=False)
        
        assert len(result) == 3
        assert result == [{"id": 1}, {"id": 2}, {"id": 3}]

    def test_format_with_transform(self):
        """Test formatting with transformation function."""
        executor = QueryExecutor()
        data = [{"name": "  John  ", "age": 30}]
        
        def transform(record):
            return {
                "name": record["name"].strip(),
                "age": record["age"]
            }
        
        result = executor.format_result(data, single=True, transform=transform)
        
        assert result == {"name": "John", "age": 30}


class TestQueryExecutorBatch:
    """Test batch query execution."""

    @patch('app.services.query_executor.neo4j')
    def test_execute_batch(self, mock_neo4j):
        """Test executing multiple queries in batch."""
        mock_driver = Mock()
        mock_session = Mock()
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        
        mock_result1 = Mock()
        mock_result1.data.return_value = [{"id": 1}]
        mock_result2 = Mock()
        mock_result2.data.return_value = [{"id": 2}]
        
        mock_session.run.side_effect = [mock_result1, mock_result2]
        
        mock_neo4j.GraphDatabase.driver.return_value = mock_driver
        
        executor = QueryExecutor()
        executor.driver = mock_driver
        
        queries = [
            "MATCH (n) WHERE n.id = 1 RETURN n.id",
            "MATCH (n) WHERE n.id = 2 RETURN n.id"
        ]
        
        results = executor.execute_batch(queries)
        
        assert len(results) == 2
        assert results[0] == [{"id": 1}]
        assert results[1] == [{"id": 2}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
