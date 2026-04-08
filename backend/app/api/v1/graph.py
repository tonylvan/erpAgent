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
from app.services.neo4j_service import neo4j_service

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
    limit: int = 100,  # Default limit reduced to 100 for better UX
    db: Session = Depends(get_db)
):
    """
    Get graph data for visualization
    
    Returns real Neo4j data when connected, otherwise mock data
    """
    try:
        if neo4j_service.connected:
            # Get all important node types - scale based on limit
            all_node_ids = set()
            
            # Calculate per-type limit based on total limit
            per_type_limit = max(10, limit // 12)  # Distribute across 12 types
            
            # Get nodes by type to ensure we have all types represented
            type_nodes = {}
            for label in ['POLine', 'Invoice', 'Payment', 'PriceList', 'Supplier', 'PurchaseOrder', 'Sale', 'Order', 'Customer', 'Event', 'Product', 'Time']:
                nodes = neo4j_service.get_nodes(label=label, limit=per_type_limit)
                type_nodes[label] = nodes
                for node in nodes:
                    all_node_ids.add(node['id'])
            
            # Limit total nodes to requested limit
            node_id_list = list(all_node_ids)[:limit]
            nodes = neo4j_service.get_nodes_by_ids(node_id_list)
            
            # Get edges - scale based on limit
            edges = neo4j_service.get_edges(limit=limit*2)
            
            # Add nodes from edges
            for edge in edges:
                if len(all_node_ids) < limit:  # Only add if within limit
                    all_node_ids.add(edge['source'])
                    all_node_ids.add(edge['target'])
            
            # Filter edges to only include those with both nodes present
            node_id_set = set(n['id'] for n in nodes)
            valid_edges = [e for e in edges if e['source'] in node_id_set and e['target'] in node_id_set][:limit]  # Limit edges too
            
            message = f"Real Neo4j data - {len(nodes)} nodes, {len(valid_edges)} edges"
            
            return GraphData(
                success=True,
                nodes=nodes,
                edges=valid_edges,
                message=message
            )
        else:
            # Mock data for demonstration
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
            
            message = "Mock data - Neo4j not connected"
        
        return GraphData(
            success=True,
            nodes=nodes,
            edges=edges,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {str(e)}")


@router.get("/nodes")
def get_nodes(limit: int = 50, db: Session = Depends(get_db)):
    """Get graph nodes from Neo4j"""
    try:
        if neo4j_service.connected:
            nodes = neo4j_service.get_nodes(limit=limit)
        else:
            nodes = [
                {"id": f"node_{i}", "name": f"Node {i}", "type": "Entity"}
                for i in range(min(limit, 50))
            ]
        return {"success": True, "nodes": nodes, "count": len(nodes), "neo4j_connected": neo4j_service.connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges")
def get_edges(limit: int = 100, db: Session = Depends(get_db)):
    """Get graph edges from Neo4j"""
    try:
        if neo4j_service.connected:
            edges = neo4j_service.get_edges(limit=limit)
        else:
            edges = [
                {"id": f"edge_{i}", "source": f"node_{i}", "target": f"node_{(i+1) % 50}", "type": "RELATED"}
                for i in range(min(limit, 100))
            ]
        return {"success": True, "edges": edges, "count": len(edges), "neo4j_connected": neo4j_service.connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_graph_stats(db: Session = Depends(get_db)):
    """Get graph statistics from Neo4j"""
    try:
        if neo4j_service.connected:
            stats = neo4j_service.get_stats()
            return {
                "success": True,
                "stats": stats,
                "neo4j_connected": True,
                "message": "Real Neo4j statistics"
            }
        else:
            return {
                "success": True,
                "stats": {
                    "nodes": 8,
                    "relationships": 8,
                    "labels": ["Customer", "Order", "Product", "Invoice"],
                    "relationship_types": ["PLACED", "CONTAINS", "GENERATES"]
                },
                "neo4j_connected": False,
                "message": "Mock statistics - Neo4j not connected"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-events")
def sync_events_to_graph(db: Session = Depends(get_db)):
    """
    Sync alerts/events to knowledge graph
    Creates Event nodes from alert data
    """
    try:
        from app.models.alert import Alert
        from sqlalchemy import desc
        
        # Get recent alerts
        alerts = db.query(Alert).order_by(desc(Alert.created_at)).limit(20).all()
        
        if not alerts:
            return {"success": True, "synced": 0, "message": "No alerts to sync"}
        
        # Convert to dict format
        events = [{
            "id": a.id,
            "title": a.title,
            "level": a.level,
            "status": a.status,
            "business_module": a.business_module,
            "description": a.description,
            "created_at": str(a.created_at) if a.created_at else None
        } for a in alerts]
        
        # Sync to Neo4j
        if neo4j_service.connected:
            synced = neo4j_service.sync_events(events)
            return {
                "success": True,
                "synced": synced,
                "total_alerts": len(alerts),
                "message": f"Synced {synced} events to knowledge graph"
            }
        else:
            return {
                "success": False,
                "synced": 0,
                "message": "Neo4j not connected"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
