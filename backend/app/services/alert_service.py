# -*- coding: utf-8 -*-
"""
Alert Service - Query real alerts from Neo4j
"""
from typing import Dict, List, Any
from datetime import datetime
from app.db.neo4j import get_neo4j


class AlertService:
    """Alert Service"""
    
    def __init__(self):
        self.neo4j = get_neo4j()
    
    def get_all_alerts(self) -> Dict[str, Any]:
        """Get all alerts"""
        if not self.neo4j.driver:
            self.neo4j.connect()
        
        alerts = {
            "inventory": self._get_inventory_alerts(),
            "payment": self._get_payment_alerts(),
            "customer": self._get_customer_alerts(),
            "supplier": self._get_supplier_alerts(),
            "financial": self._get_financial_alerts()
        }
        
        stats = self._calculate_stats(alerts)
        
        return {
            "alerts": alerts,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_inventory_alerts(self) -> List[Dict[str, Any]]:
        """Inventory alerts"""
        cypher = """
        MATCH (p:Product)
        WHERE p.current_stock IS NOT NULL AND p.safety_stock IS NOT NULL
        AND p.current_stock < p.safety_stock
        RETURN 
            p.id AS id,
            p.name AS product_name,
            p.current_stock AS current_stock,
            p.safety_stock AS safety_stock,
            p.category AS category,
            CASE 
                WHEN p.current_stock < p.safety_stock * 0.5 THEN 'RED'
                WHEN p.current_stock < p.safety_stock * 0.8 THEN 'ORANGE'
                ELSE 'YELLOW'
            END AS severity,
            'Inventory low: ' + p.name + ' (Current: ' + toString(p.current_stock) + ', Safety: ' + toString(p.safety_stock) + ')' AS description,
            'Reorder immediately' AS recommendation
        ORDER BY p.current_stock * 1.0 / p.safety_stock ASC
        LIMIT 20
        """
        
        results = self.neo4j.query(cypher)
        
        alerts = []
        for row in results:
            alerts.append({
                "id": row.get("id"),
                "type": "inventory_low",
                "severity": row.get("severity", "YELLOW"),
                "product_name": row.get("product_name"),
                "current_stock": row.get("current_stock"),
                "safety_stock": row.get("safety_stock"),
                "description": row.get("description"),
                "recommendation": row.get("recommendation"),
                "created_at": datetime.now().isoformat()
            })
        
        return alerts
    
    def _get_payment_alerts(self) -> List[Dict[str, Any]]:
        """Payment alerts"""
        cypher = """
        MATCH (po:PurchaseOrder)-[:HAS_PAYMENT]->(p:Payment)
        WHERE p.status IN ['PENDING', 'OVERDUE']
        AND p.due_date IS NOT NULL
        AND p.due_date < date()
        RETURN 
            p.id AS id,
            p.payment_number AS payment_number,
            po.po_number AS po_number,
            p.amount AS amount,
            p.due_date AS due_date,
            duration.inDays(p.due_date, date()).days AS overdue_days,
            CASE 
                WHEN duration.inDays(p.due_date, date()).days > 30 THEN 'RED'
                WHEN duration.inDays(p.due_date, date()).days > 7 THEN 'ORANGE'
                ELSE 'YELLOW'
            END AS severity,
            'Payment overdue: ' + p.payment_number + ' (' + toString(duration.inDays(p.due_date, date()).days) + ' days)' AS description,
            'Arrange payment immediately' AS recommendation
        ORDER BY overdue_days DESC
        LIMIT 20
        """
        
        results = self.neo4j.query(cypher)
        
        alerts = []
        for row in results:
            alerts.append({
                "id": row.get("id"),
                "type": "payment_overdue",
                "severity": row.get("severity", "YELLOW"),
                "payment_number": row.get("payment_number"),
                "po_number": row.get("po_number"),
                "amount": row.get("amount"),
                "overdue_days": row.get("overdue_days"),
                "description": row.get("description"),
                "recommendation": row.get("recommendation"),
                "created_at": datetime.now().isoformat()
            })
        
        return alerts
    
    def _get_customer_alerts(self) -> List[Dict[str, Any]]:
        """Customer alerts (AR overdue)"""
        cypher = """
        MATCH (c:Customer)-[:HAS_INVOICE]->(i:Invoice)
        WHERE i.status = 'OVERDUE'
        AND i.due_date IS NOT NULL
        AND i.due_date < date()
        WITH c, i, duration.inDays(i.due_date, date()).days AS overdue_days
        RETURN 
            c.id AS customer_id,
            c.name AS customer_name,
            count(i) AS overdue_count,
            sum(i.amount) AS total_overdue,
            max(overdue_days) AS max_overdue_days,
            CASE 
                WHEN max(overdue_days) > 60 THEN 'RED'
                WHEN max(overdue_days) > 30 THEN 'ORANGE'
                ELSE 'YELLOW'
            END AS severity,
            'Customer ' + c.name + ' has ' + toString(count(i)) + ' overdue invoices' AS description,
            'Contact customer for collection' AS recommendation
        GROUP BY c
        ORDER BY total_overdue DESC
        LIMIT 20
        """
        
        results = self.neo4j.query(cypher)
        
        alerts = []
        for row in results:
            alerts.append({
                "id": row.get("customer_id"),
                "type": "customer_overdue",
                "severity": row.get("severity", "YELLOW"),
                "customer_name": row.get("customer_name"),
                "overdue_count": row.get("overdue_count"),
                "total_overdue": row.get("total_overdue"),
                "max_overdue_days": row.get("max_overdue_days"),
                "description": row.get("description"),
                "recommendation": row.get("recommendation"),
                "created_at": datetime.now().isoformat()
            })
        
        return alerts
    
    def _get_supplier_alerts(self) -> List[Dict[str, Any]]:
        """Supplier alerts (delivery delay)"""
        cypher = """
        MATCH (po:PurchaseOrder)-[:FROM_SUPPLIER]->(s:Supplier)
        WHERE po.status = 'PENDING'
        AND po.expected_delivery_date IS NOT NULL
        AND po.expected_delivery_date < date()
        RETURN 
            s.id AS supplier_id,
            s.name AS supplier_name,
            po.po_number AS po_number,
            po.expected_delivery_date AS expected_date,
            duration.inDays(po.expected_delivery_date, date()).days AS delay_days,
            CASE 
                WHEN duration.inDays(po.expected_delivery_date, date()).days > 14 THEN 'RED'
                WHEN duration.inDays(po.expected_delivery_date, date()).days > 7 THEN 'ORANGE'
                ELSE 'YELLOW'
            END AS severity,
            'Supplier ' + s.name + ' delivery delayed: ' + po.po_number + ' (' + toString(duration.inDays(po.expected_delivery_date, date()).days) + ' days)' AS description,
            'Contact supplier for delivery confirmation' AS recommendation
        ORDER BY delay_days DESC
        LIMIT 20
        """
        
        results = self.neo4j.query(cypher)
        
        alerts = []
        for row in results:
            alerts.append({
                "id": row.get("supplier_id"),
                "type": "supplier_delay",
                "severity": row.get("severity", "YELLOW"),
                "supplier_name": row.get("supplier_name"),
                "po_number": row.get("po_number"),
                "delay_days": row.get("delay_days"),
                "description": row.get("description"),
                "recommendation": row.get("recommendation"),
                "created_at": datetime.now().isoformat()
            })
        
        return alerts
    
    def _get_financial_alerts(self) -> List[Dict[str, Any]]:
        """Financial risk alerts"""
        # Simplified: Check cash balance
        cash_query = """
        MATCH (c:CashAccount)
        WHERE c.balance IS NOT NULL
        RETURN c.balance AS balance
        """
        cash_results = self.neo4j.query(cash_query)
        
        alerts = []
        
        if cash_results and len(cash_results) > 0:
            total_cash = sum(r.get("balance", 0) for r in cash_results)
            if total_cash < 1000000:  # 1M safety line
                alerts.append({
                    "id": "cashflow_risk",
                    "type": "cashflow_critical",
                    "severity": "RED",
                    "description": f"Cash flow critical: Current balance {total_cash/10000:.1f}K, below safety line 1M",
                    "recommendation": "Accelerate collection, defer non-essential payments",
                    "data": {
                        "current_cash": total_cash,
                        "safety_line": 1000000
                    },
                    "created_at": datetime.now().isoformat()
                })
        
        return alerts
    
    def _calculate_stats(self, alerts: Dict[str, List]) -> Dict[str, Any]:
        """Calculate statistics"""
        all_alerts = []
        for alert_list in alerts.values():
            all_alerts.extend(alert_list)
        
        stats = {
            "total": len(all_alerts),
            "by_severity": {
                "RED": sum(1 for a in all_alerts if a.get("severity") == "RED"),
                "ORANGE": sum(1 for a in all_alerts if a.get("severity") == "ORANGE"),
                "YELLOW": sum(1 for a in all_alerts if a.get("severity") == "YELLOW"),
            },
            "financial_risks": len(alerts.get("financial", [])),
            "business_alerts": (len(alerts.get("inventory", [])) + 
                               len(alerts.get("payment", [])) + 
                               len(alerts.get("customer", [])) + 
                               len(alerts.get("supplier", [])))
        }
        
        return stats


# Global service instance
alert_service = AlertService()


def get_alert_service() -> AlertService:
    """Get alert service instance"""
    return alert_service
