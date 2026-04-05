"""业务风险 Agent - 封装现有业务预警规则"""
import logging
from datetime import datetime
from typing import Any, Dict, List
from neo4j import Driver
from app.services.alert_rules import AlertRuleEngine

logger = logging.getLogger(__name__)

class BusinessRiskAgent:
    def __init__(self, neo4j_driver: Driver):
        self.driver = neo4j_driver
        self.engine = AlertRuleEngine(neo4j_driver)
        self.agent_name = "business_risk"
        self.agent_version = "1.0.0"
    
    def analyze(self) -> List[Dict[str, Any]]:
        logger.info("BusinessRiskAgent: Starting analysis...")
        findings = []
        try:
            findings.extend(self._format(self.engine.check_inventory_low(), "INVENTORY_LOW", "MEDIUM"))
            findings.extend(self._format(self.engine.check_inventory_zero(), "INVENTORY_ZERO", "CRITICAL"))
            findings.extend(self._format(self.engine.check_payment_overdue(), "PAYMENT_OVERDUE", "HIGH"))
            findings.extend(self._format(self.engine.check_customer_churn(), "CUSTOMER_CHURN", "HIGH"))
            findings.extend(self._format(self.engine.check_delivery_delay(), "SUPPLIER_DELAY", "MEDIUM"))
            findings.extend(self._format(self.engine.check_sales_anomaly(), "SALES_ANOMALY", "MEDIUM"))
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            findings.append({"risk_id": "error", "risk_type": "AGENT_ERROR", "severity": "CRITICAL", "entity_id": None, "entity_name": "BusinessRiskAgent", "description": str(e), "recommendation": "检查连接", "data": {}, "detected_at": datetime.now().isoformat()})
        return findings
    
    def _format(self, alerts: List[Dict], risk_type: str, default_sev: str) -> List[Dict[str, Any]]:
        sev_map = {"RED": "CRITICAL", "ORANGE": "HIGH", "YELLOW": "MEDIUM", "GREEN": "LOW"}
        return [{"risk_id": f"{self.agent_name}_{risk_type.lower()}_{(a.get('product_id') or a.get('invoice_id') or a.get('customer_id') or 'x')}_{i}", "risk_type": risk_type, "severity": sev_map.get(a.get("severity", default_sev), default_sev), "entity_id": a.get("product_id") or a.get("invoice_id") or a.get("customer_id") or "x", "entity_name": a.get("product_name") or a.get("invoice_number") or a.get("customer_name") or "Unknown", "description": a.get("description", ""), "recommendation": a.get("recommendation", ""), "data": {k:v for k,v in a.items() if k not in ["alert_type","severity","description","recommendation"]}, "detected_at": datetime.now().isoformat(), "agent": self.agent_name, "agent_version": self.agent_version} for i, a in enumerate(alerts)]
    
    def get_summary(self) -> Dict[str, Any]:
        f = self.analyze()
        return {"agent": self.agent_name, "version": self.agent_version, "total": len(f), "by_severity": {s: sum(1 for x in f if x["severity"]==s) for s in ["CRITICAL","HIGH","MEDIUM","LOW"]}, "timestamp": datetime.now().isoformat()}

def create_business_risk_agent(driver: Driver) -> BusinessRiskAgent:
    return BusinessRiskAgent(driver)
