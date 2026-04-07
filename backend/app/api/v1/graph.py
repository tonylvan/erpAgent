"""
Knowledge Graph API routes
Provides Neo4j graph data for visualization
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Knowledge Graph"])


class GraphNode(BaseModel):
    """Graph node model"""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class GraphEdge(BaseModel):
    """Graph edge model"""
    id: str
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class GraphData(BaseModel):
    """Graph data response"""
    success: bool
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    message: str


@router.get("/", response_model=GraphData)
def get_graph_data(
    entity_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get graph data for visualization
    
    Returns mock data when Neo4j is not available
    """
    try:
        # Mock data for demonstration (replace with Neo4j query when available)
        nodes = [
            {"id": "customer_1", "name": "ABC Corp", "type": "Customer", "description": "Key customer"},
            {"id": "customer_2", "name": "XYZ Ltd", "type": "Customer", "description": "Regular customer"},
            {"id": "order_1", "name": "Order SO-2026-001", "type": "Order", "description": "Sales order"},
            {"id": "order_2", "name": "Order SO-2026-002", "type": "Order", "description": "Sales order"},
            {"id": "product_1", "name": "Product A001", "type": "Product", "description": "Main product"},
            {"id": "product_2", "name": "Product B002", "type": "Product", "description": "Secondary product"},
            {"id": "invoice_1", "name": "Invoice INV-2026-001", "type": "Invoice", "description": "Sales invoice"},
            {"id": "invoice_2", "name": "Invoice INV-2026-002", "type": "Invoice", "description": "Sales invoice"},
        ][:limit]
        
        edges = [
            {"id": "edge_1", "source": "customer_1", "target": "order_1", "type": "PLACED"},
            {"id": "edge_2", "source": "customer_1", "target": "order_2", "type": "PLACED"},
            {"id": "edge_3", "source": "customer_2", "target": "order_1", "type": "PLACED"},
            {"id": "edge_4", "source": "order_1", "target": "product_1", "type": "CONTAINS"},
            {"id": "edge_5", "source": "order_1", "target": "product_2", "type": "CONTAINS"},
            {"id": "edge_6", "source": "order_2", "target": "product_1", "type": "CONTAINS"},
            {"id": "edge_7", "source": "order_1", "target": "invoice_1", "type": "GENERATES"},
            {"id": "edge_8", "source": "order_2", "target": "invoice_2", "type": "GENERATES"},
        ][:limit]
        
        return GraphData(
            success=True,
            nodes=nodes,
            edges=edges,
            message="Graph data retrieved successfully (mock data - Neo4j not connected)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {str(e)}")


@router.get("/nodes")
def get_nodes(limit: int = 50, db: Session = Depends(get_db)):
    """Get graph nodes"""
    try:
        # Mock data
        nodes = [
            {"id": f"node_{i}", "name": f"Node {i}", "type": "Entity"}
            for i in range(min(limit, 50))
        ]
        return {"success": True, "nodes": nodes, "count": len(nodes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges")
def get_edges(limit: int = 100, db: Session = Depends(get_db)):
    """Get graph edges"""
    try:
        # Mock data
        edges = [
            {"id": f"edge_{i}", "source": f"node_{i}", "target": f"node_{(i+1) % 50}", "type": "RELATED"}
            for i in range(min(limit, 100))
        ]
        return {"success": True, "edges": edges, "count": len(edges)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_graph_stats(db: Session = Depends(get_db)):
    """Get graph statistics"""
    try:
        return {
            "success": True,
            "stats": {
                "total_nodes": 8,
                "total_edges": 8,
                "node_types": ["Customer", "Order", "Product", "Invoice"],
                "edge_types": ["PLACED", "CONTAINS", "GENERATES"],
                "neo4j_connected": False,
                "message": "Using mock data - Neo4j not connected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
