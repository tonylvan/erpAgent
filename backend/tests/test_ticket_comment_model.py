"""Ticket Comment Model Tests - TDD Approach"""

import pytest
from sqlalchemy import inspect
from app.db.database import engine, SessionLocal
from app.models.ticket_comment import TicketComment
# Import Ticket model to ensure the foreign key relationship is registered
from app.models.ticket import Ticket


class TestTicketCommentModelExists:
    """Test that TicketComment model exists and has correct structure"""
    
    def test_ticket_comment_class_exists(self):
        """Test that TicketComment class is defined"""
        assert TicketComment is not None
        assert hasattr(TicketComment, '__tablename__')
        assert TicketComment.__tablename__ == 'ticket_comments'
    
    def test_ticket_comment_has_id_field(self):
        """Test that model has id primary key field"""
        assert hasattr(TicketComment, 'id')
    
    def test_ticket_comment_has_ticket_id_field(self):
        """Test that model has ticket_id foreign key field"""
        assert hasattr(TicketComment, 'ticket_id')
    
    def test_ticket_comment_has_content_field(self):
        """Test that model has content field"""
        assert hasattr(TicketComment, 'content')
    
    def test_ticket_comment_has_author_field(self):
        """Test that model has author field"""
        assert hasattr(TicketComment, 'author')
    
    def test_ticket_comment_has_author_role_field(self):
        """Test that model has author_role field"""
        assert hasattr(TicketComment, 'author_role')
    
    def test_ticket_comment_has_is_internal_field(self):
        """Test that model has is_internal field"""
        assert hasattr(TicketComment, 'is_internal')
    
    def test_ticket_comment_has_attachments_field(self):
        """Test that model has attachments field"""
        assert hasattr(TicketComment, 'attachments')
    
    def test_ticket_comment_has_created_at_field(self):
        """Test that model has created_at field"""
        assert hasattr(TicketComment, 'created_at')
    
    def test_ticket_comment_has_updated_at_field(self):
        """Test that model has updated_at field"""
        assert hasattr(TicketComment, 'updated_at')
    
    def test_ticket_comment_has_to_dict_method(self):
        """Test that model has to_dict method"""
        assert hasattr(TicketComment, 'to_dict')
        assert callable(getattr(TicketComment, 'to_dict'))


class TestTicketCommentDatabaseTable:
    """Test that database table exists with correct structure"""
    
    @pytest.fixture
    def db_session(self):
        """Create database session"""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_ticket_comments_table_exists(self, db_session):
        """Test that ticket_comments table exists in database"""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert 'ticket_comments' in tables
    
    def test_ticket_comments_table_columns(self, db_session):
        """Test that ticket_comments table has correct columns"""
        inspector = inspect(engine)
        columns = inspector.get_columns('ticket_comments')
        column_names = [col['name'] for col in columns]
        
        expected_columns = [
            'id', 'ticket_id', 'content', 'author', 'author_role',
            'is_internal', 'attachments', 'created_at', 'updated_at'
        ]
        
        for col_name in expected_columns:
            assert col_name in column_names, f"Column {col_name} missing from table"
    
    def test_ticket_comments_table_index_exists(self, db_session):
        """Test that index on ticket_id exists"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('ticket_comments')
        index_names = [idx['name'] for idx in indexes]
        
        # Check if any index name contains 'ticket_id'
        ticket_id_indexes = [name for name in index_names if 'ticket_id' in name]
        assert len(ticket_id_indexes) > 0, "Index on ticket_id not found"


class TestTicketCommentInstance:
    """Test TicketComment model instance creation and methods"""
    
    @pytest.fixture
    def db_session(self):
        """Create database session"""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_create_ticket_comment_basic(self, db_session):
        """Test creating a basic ticket comment"""
        comment = TicketComment(
            ticket_id=1,
            content="This is a test comment",
            author="John Doe",
            author_role="Developer"
        )
        
        assert comment.ticket_id == 1
        assert comment.content == "This is a test comment"
        assert comment.author == "John Doe"
        assert comment.author_role == "Developer"
        assert comment.attachments is None
        
        # Test default value after adding to session
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        assert comment.is_internal is True  # Default value from database
    
    def test_create_ticket_comment_with_attachments(self, db_session):
        """Test creating comment with attachments"""
        attachments = [
            {"filename": "screenshot.png", "url": "/files/1.png"},
            {"filename": "log.txt", "url": "/files/1.txt"}
        ]
        
        comment = TicketComment(
            ticket_id=2,
            content="Comment with attachments",
            author="Jane Smith",
            author_role="Manager",
            attachments=attachments,
            is_internal=False
        )
        
        assert comment.ticket_id == 2
        assert comment.content == "Comment with attachments"
        assert comment.author == "Jane Smith"
        assert comment.author_role == "Manager"
        assert comment.is_internal is False
        assert comment.attachments == attachments
    
    def test_ticket_comment_to_dict(self, db_session):
        """Test converting comment to dictionary"""
        comment = TicketComment(
            ticket_id=3,
            content="Test comment",
            author="Test User",
            author_role="Tester"
        )
        comment.id = 1  # Simulate database-generated ID
        
        comment_dict = comment.to_dict()
        
        assert comment_dict['id'] == 1
        assert comment_dict['ticket_id'] == 3
        assert comment_dict['content'] == "Test comment"
        assert comment_dict['author'] == "Test User"
        assert comment_dict['author_role'] == "Tester"
        assert 'created_at' in comment_dict
        assert 'updated_at' in comment_dict
    
    def test_ticket_comment_default_is_internal(self, db_session):
        """Test that is_internal defaults to True"""
        comment = TicketComment(
            ticket_id=4,
            content="Internal comment",
            author="Admin"
        )
        
        # Add to session to get default value from database
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        assert comment.is_internal is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
