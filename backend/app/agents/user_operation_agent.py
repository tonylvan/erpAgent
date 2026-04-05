"""用户操作 Agent - 检测用户操作异常"""
import logging
from datetime import datetime
from typing import Any, Dict, List
from neo4j import Driver

logger = logging.getLogger(__name__)

class UserOperationAgent:
    def __init__(self, neo4j_driver: Driver):
        self.driver = neo4j_driver
        self.agent_name = "user_operation"
        self.agent_version = "1.0.0"
        self.config = {"approval_timeout_hours": 48, "ticket_overdue_days": 3, "frequent_mod_threshold": 10}
    
    def analyze(self) -> List[Dict[str, Any]]:
        logger.info("UserOperationAgent: Starting analysis...")
        findings = []
        try:
            findings.extend(self._check_approval_timeout())
            findings.extend(self._check_ticket_overdue())
            findings.extend(self._check_frequent_modifications())
            findings.extend(self._check_unauthorized_access())
            findings.extend(self._check_missing_fields())
            findings.extend(self._check_duplicate_entries())
            findings.extend(self._check_low_feature_adoption())
            findings.extend(self._check_high_error_rate())
            findings.extend(self._check_off_hours_operation())
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            findings.append({"risk_id": "error", "risk_type": "AGENT_ERROR", "severity": "CRITICAL", "entity_id": None, "entity_name": "UserOperationAgent", "description": str(e), "recommendation": "检查连接", "data": {}, "detected_at": datetime.now().isoformat()})
        return findings
    
    def _check_approval_timeout(self) -> List[Dict[str, Any]]:
        cypher = f"MATCH (a:ApprovalRequest) WHERE a.status='PENDING' AND a.submitted_at < datetime()-duration({{hours:{self.config['approval_timeout_hours']}}}) OPTIONAL MATCH (a)-[:ASSIGNED_TO]->(u:User) RETURN a.id,a.request_type,a.request_number,duration.inMinutes(a.submitted_at,datetime()).minutes/60 as overdue,COALESCE(u.username,'Unassigned') as approver LIMIT 50"
        return self._run_query(cypher, "APPROVAL_TIMEOUT", "HIGH", lambda r: {"request_type": r.get("request_type"), "overdue_hours": round(r.get("overdue",0),2), "approver": r.get("approver")})
    
    def _check_ticket_overdue(self) -> List[Dict[str, Any]]:
        cypher = f"MATCH (t:Ticket) WHERE t.status NOT IN ['CLOSED','RESOLVED'] AND t.created_at < datetime()-duration({{days:{self.config['ticket_overdue_days']}}}) RETURN t.id,t.ticket_number,t.priority,duration.inDays(t.created_at,datetime()).days as age LIMIT 50"
        return self._run_query(cypher, "TICKET_OVERDUE", "HIGH", lambda r: {"priority": r.get("priority"), "age_days": r.get("age")})
    
    def _check_frequent_modifications(self) -> List[Dict[str, Any]]:
        cypher = f"MATCH (u:User)-[r:MODIFIED]->(e) WHERE r.timestamp>=datetime()-duration({{hours:1}}) WITH u,e,count(r) as c WHERE c>={self.config['frequent_mod_threshold']} RETURN u.id,u.username,labels(e)[0] as type,c ORDER BY c DESC LIMIT 20"
        return self._run_query(cypher, "FREQUENT_MODIFICATIONS", "HIGH", lambda r: {"count": r.get("c"), "entity_type": r.get("type")})
    
    def _check_unauthorized_access(self) -> List[Dict[str, Any]]:
        cypher = "MATCH (u:User)-[r:ATTEMPTED_ACCESS]->(e) WHERE r.granted=false AND r.timestamp>=datetime()-duration({hours:24}) WITH u,e,count(r) as c WHERE c>=3 RETURN u.id,u.username,u.role,c ORDER BY c DESC LIMIT 20"
        return self._run_query(cypher, "UNAUTHORIZED_ACCESS", "CRITICAL", lambda r: {"role": r.get("role"), "denied_count": r.get("c")})
    
    def _check_missing_fields(self) -> List[Dict[str, Any]]:
        cypher = "MATCH (e) WHERE labels(e)[0] IN ['Customer','Supplier','Product'] AND (e.name IS NULL OR e.contact_info IS NULL) RETURN id(e) as eid,labels(e)[0] as type LIMIT 50"
        return self._run_query(cypher, "MISSING_FIELDS", "MEDIUM", lambda r: {"entity_type": r.get("type")})
    
    def _check_duplicate_entries(self) -> List[Dict[str, Any]]:
        cypher = "MATCH (e:Customer) WHERE e.customer_name IS NOT NULL WITH e.customer_name as n,collect(e) as c WHERE size(c)>1 RETURN 'Customer' as type,n,size(c) as cnt,[x in c|id(x)] as ids LIMIT 20"
        return self._run_query(cypher, "DUPLICATE_ENTRIES", "MEDIUM", lambda r: {"duplicate_count": r.get("cnt"), "entity_ids": r.get("ids")})
    
    def _check_low_feature_adoption(self) -> List[Dict[str, Any]]:
        cypher = "MATCH (f:Feature) WHERE f.deployed=true OPTIONAL MATCH (u:User)-[:USED]->(f) WHERE u.active=true WITH f,count(DISTINCT u) as u,f.total_licensed_users as t WHERE t>0 WITH f,u,t,toFloat(u)/toFloat(t) as r WHERE r<0.3 RETURN f.id,f.name,u,t,r*100 as pct LIMIT 20"
        return self._run_query(cypher, "LOW_FEATURE_ADOPTION", "LOW", lambda r: {"usage_percent": round(r.get("pct",0),2), "active": r.get("u"), "total": r.get("t")})
    
    def _check_high_error_rate(self) -> List[Dict[str, Any]]:
        cypher = "MATCH (e:ErrorLog) WHERE e.timestamp>=datetime()-duration({hours:24}) WITH e.endpoint,count(*) as c,sum(CASE WHEN e.severity IN ['ERROR','CRITICAL'] THEN 1 ELSE 0 END) as err WHERE c>10 WITH endpoint,c,err,toFloat(err)/toFloat(c) as r WHERE r>0.1 RETURN endpoint,c,err,r*100 as pct ORDER BY r DESC LIMIT 20"
        return self._run_query(cypher, "HIGH_ERROR_RATE", "HIGH", lambda r: {"error_percent": round(r.get("pct",0),2), "total": r.get("c"), "errors": r.get("err")})
    
    def _check_off_hours_operation(self) -> List[Dict[str, Any]]:
        cypher = "MATCH (u:User)-[r:MODIFIED|CREATED|DELETED]->(e) WHERE r.timestamp IS NOT NULL WITH u,count(*) as c WHERE c>=3 RETURN u.id,u.username,c ORDER BY c DESC LIMIT 20"
        return self._run_query(cypher, "OFF_HOURS_OPERATION", "MEDIUM", lambda r: {"operation_count": r.get("c")})
    
    def _run_query(self, cypher: str, risk_type: str, severity: str, data_fn) -> List[Dict[str, Any]]:
        findings = []
        try:
            with self.driver.session() as session:
                for r in session.run(cypher):
                    eid = r.get(r.keys()[0]) if r.keys() else "x"
                    ename = r.get(r.keys()[1]) if len(r.keys()) > 1 else str(eid)
                    findings.append({"risk_id": f"{self.agent_name}_{risk_type.lower()}_{eid}", "risk_type": risk_type, "severity": severity, "entity_id": eid, "entity_name": ename, "description": f"检测到{risk_type}", "recommendation": "需要审查", "data": data_fn(r), "detected_at": datetime.now().isoformat(), "agent": self.agent_name, "agent_version": self.agent_version})
        except Exception as e:
            logger.error(f"Query failed for {risk_type}: {e}")
        return findings
    
    def get_summary(self) -> Dict[str, Any]:
        f = self.analyze()
        return {"agent": self.agent_name, "version": self.agent_version, "total": len(f), "by_severity": {s: sum(1 for x in f if x["severity"]==s) for s in ["CRITICAL","HIGH","MEDIUM","LOW"]}, "timestamp": datetime.now().isoformat()}

def create_user_operation_agent(driver: Driver) -> UserOperationAgent:
    return UserOperationAgent(driver)
