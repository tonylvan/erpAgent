"""预警中心集成服务 - 实现预警自动生成工单"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import uuid

logger = logging.getLogger(__name__)


class AlertTicketMapping(BaseModel):
    """预警 - 工单映射"""
    id: str = Field(..., description="映射 ID")
    alert_id: str = Field(..., description="预警 ID")
    ticket_id: str = Field(..., description="工单 ID")
    alert_type: str = Field(..., description="预警类型")
    auto_created: bool = Field(default=False, description="是否自动创建")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    created_by: Optional[str] = Field(None, description="创建人")


class AlertIntegrationService:
    """预警中心集成服务"""
    
    def __init__(self, ticket_service=None, db_session=None):
        """
        初始化集成服务
        
        Args:
            ticket_service: 工单服务
            db_session: 数据库会话
        """
        self.ticket_service = ticket_service
        self.db = db_session
        self.mappings: List[AlertTicketMapping] = []
    
    def create_ticket_from_alert(
        self,
        alert: Dict[str, Any],
        auto_create: bool = False,
        created_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从预警创建工单
        
        Args:
            alert: 预警信息
            auto_create: 是否自动创建
            created_by: 创建人 ID
            
        Returns:
            Dict: 工单信息
        """
        try:
            # 1. 检查是否已存在映射
            existing = self._find_mapping(alert["id"])
            if existing:
                logger.info(f"预警 {alert['id']} 已有关联工单：{existing.ticket_id}")
                return None
            
            # 2. 确定工单优先级
            priority = self._determine_priority(alert)
            
            # 3. 确定问题类型
            issue_type = self._determine_issue_type(alert)
            
            # 4. 生成工单标题和描述
            title = self._generate_title(alert)
            description = self._generate_description(alert)
            
            # 5. 创建工单
            ticket_data = {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "priority": priority,
                "issue_type": issue_type,
                "alert_id": alert["id"],
                "related_entities": alert.get("related_entities", {}),
                "created_by": created_by,
                "auto_created": auto_create
            }
            
            # 6. 调用工单服务创建（这里简化处理）
            # ticket = self.ticket_service.create(ticket_data)
            
            # 7. 创建映射关系
            mapping = AlertTicketMapping(
                id=str(uuid.uuid4()),
                alert_id=alert["id"],
                ticket_id=ticket_data["id"],
                alert_type=alert.get("type", "UNKNOWN"),
                auto_created=auto_create,
                created_by=created_by
            )
            self.mappings.append(mapping)
            
            logger.info(f"从预警创建工单：{alert['id']} -> {ticket_data['id']}")
            return ticket_data
        
        except Exception as e:
            logger.error(f"从预警创建工单失败：{e}")
            return None
    
    def _determine_priority(self, alert: Dict[str, Any]) -> str:
        """
        根据预警严重程度确定工单优先级
        
        Args:
            alert: 预警信息
            
        Returns:
            str: 优先级
        """
        severity = alert.get("severity", "MEDIUM")
        
        priority_mapping = {
            "CRITICAL": "URGENT",
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW"
        }
        
        return priority_mapping.get(severity, "MEDIUM")
    
    def _determine_issue_type(self, alert: Dict[str, Any]) -> str:
        """
        根据预警类型确定问题类型
        
        Args:
            alert: 预警信息
            
        Returns:
            str: 问题类型
        """
        alert_type = alert.get("type", "UNKNOWN")
        
        issue_type_mapping = {
            "INVENTORY_WARNING": "库存异常",
            "PAYMENT_OVERDUE": "付款逾期",
            "CUSTOMER_CHURN": "客户流失",
            "DELIVERY_OVERDUE": "交货逾期",
            "SALES_ANOMALY": "销售异常",
            "CASH_FLOW_RISK": "财务风险",
            "ACCOUNT_RECEIVABLE_RISK": "应收账款风险",
            "BUDGET_DEVIATION": "预算偏差"
        }
        
        return issue_type_mapping.get(alert_type, "其他")
    
    def _generate_title(self, alert: Dict[str, Any]) -> str:
        """
        生成工单标题
        
        Args:
            alert: 预警信息
            
        Returns:
            str: 工单标题
        """
        alert_type = alert.get("type", "预警")
        severity = alert.get("severity", "MEDIUM")
        entity_name = alert.get("entity_name", "未知实体")
        
        severity_map = {
            "CRITICAL": "【紧急】",
            "HIGH": "【重要】",
            "MEDIUM": "【警告】",
            "LOW": "【提示】"
        }
        
        prefix = severity_map.get(severity, "")
        return f"{prefix}{alert_type} - {entity_name}"
    
    def _generate_description(self, alert: Dict[str, Any]) -> str:
        """
        生成工单描述
        
        Args:
            alert: 预警信息
            
        Returns:
            str: 工单描述
        """
        description = f"""
**预警来源**: 预警中心自动生成

**预警类型**: {alert.get('type', '未知')}

**预警级别**: {alert.get('severity', '未知')}

**预警内容**:
{alert.get('content', '无')}

**相关实体**:
{self._format_entities(alert.get('related_entities', {}))}

**建议措施**:
{alert.get('suggestion', '请及时处理')}

**触发时间**: {alert.get('created_at', datetime.now().isoformat())}
        """.strip()
        
        return description
    
    def _format_entities(self, entities: Dict[str, Any]) -> str:
        """格式化相关实体"""
        if not entities:
            return "无"
        
        lines = []
        for key, value in entities.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _find_mapping(self, alert_id: str) -> Optional[AlertTicketMapping]:
        """查找预警 - 工单映射"""
        for mapping in self.mappings:
            if mapping.alert_id == alert_id:
                return mapping
        return None
    
    def get_linked_tickets(self, alert_id: str) -> List[str]:
        """
        获取预警关联的所有工单
        
        Args:
            alert_id: 预警 ID
            
        Returns:
            List[str]: 工单 ID 列表
        """
        mappings = [m for m in self.mappings if m.alert_id == alert_id]
        return [m.ticket_id for m in mappings]
    
    def get_linked_alerts(self, ticket_id: str) -> List[str]:
        """
        获取工单关联的所有预警
        
        Args:
            ticket_id: 工单 ID
            
        Returns:
            List[str]: 预警 ID 列表
        """
        mappings = [m for m in self.mappings if m.ticket_id == ticket_id]
        return [m.alert_id for m in mappings]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取集成统计信息"""
        total_mappings = len(self.mappings)
        auto_created = len([m for m in self.mappings if m.auto_created])
        manual_created = total_mappings - auto_created
        
        return {
            "total_mappings": total_mappings,
            "auto_created": auto_created,
            "manual_created": manual_created,
            "by_alert_type": self._count_by_alert_type()
        }
    
    def _count_by_alert_type(self) -> Dict[str, int]:
        """按预警类型统计"""
        stats = {}
        for mapping in self.mappings:
            alert_type = mapping.alert_type
            stats[alert_type] = stats.get(alert_type, 0) + 1
        return stats


class SmartQueryIntegration:
    """智能问数集成服务"""
    
    def __init__(self, ticket_service=None):
        """
        初始化集成服务
        
        Args:
            ticket_service: 工单服务
        """
        self.ticket_service = ticket_service
        self.query_templates = self._load_query_templates()
    
    def _load_query_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载查询模板"""
        return {
            "inventory_analysis": {
                "name": "库存分析",
                "description": "分析库存周转率、呆滞料等",
                "suggested_actions": ["创建库存预警工单", "分配给库存管理员"]
            },
            "sales_analysis": {
                "name": "销售分析",
                "description": "分析销售趋势、异常订单等",
                "suggested_actions": ["创建销售异常工单", "通知销售经理"]
            },
            "financial_analysis": {
                "name": "财务分析",
                "description": "分析现金流、应收账款等",
                "suggested_actions": ["创建财务风险工单", "通知财务负责人"]
            },
            "customer_analysis": {
                "name": "客户分析",
                "description": "分析客户流失、满意度等",
                "suggested_actions": ["创建客户维护工单", "分配给客户经理"]
            }
        }
    
    def generate_ticket_suggestion(
        self,
        query_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        根据智能问数结果生成工单建议
        
        Args:
            query_result: 查询结果
            
        Returns:
            Dict: 工单建议
        """
        analysis_type = query_result.get("type")
        template = self.query_templates.get(analysis_type)
        
        if not template:
            return None
        
        # 分析数据，判断是否需要创建工单
        should_create = self._should_create_ticket(query_result)
        
        if not should_create:
            return None
        
        # 生成工单建议
        suggestion = {
            "should_create": True,
            "title": f"[智能问数] {template['name']}异常",
            "description": self._generate_description(query_result, template),
            "priority": self._determine_priority(query_result),
            "issue_type": template['name'],
            "suggested_actions": template['suggested_actions'],
            "confidence": self._calculate_confidence(query_result)
        }
        
        return suggestion
    
    def _should_create_ticket(self, query_result: Dict[str, Any]) -> bool:
        """判断是否需要创建工单"""
        # 根据查询结果的指标判断
        metrics = query_result.get("metrics", {})
        
        # 示例：如果异常率超过阈值，创建工单
        anomaly_rate = metrics.get("anomaly_rate", 0)
        if anomaly_rate > 0.1:  # 10% 异常率
            return True
        
        # 示例：如果关键指标异常
        if metrics.get("is_critical", False):
            return True
        
        return False
    
    def _determine_priority(self, query_result: Dict[str, Any]) -> str:
        """确定优先级"""
        impact = query_result.get("impact", "MEDIUM")
        
        priority_mapping = {
            "HIGH": "URGENT",
            "MEDIUM": "HIGH",
            "LOW": "MEDIUM"
        }
        
        return priority_mapping.get(impact, "MEDIUM")
    
    def _generate_description(
        self,
        query_result: Dict[str, Any],
        template: Dict[str, Any]
    ) -> str:
        """生成工单描述"""
        description = f"""
**分析来源**: 智能问数 - {template['name']}

**分析描述**: {template['description']}

**关键指标**:
{self._format_metrics(query_result.get('metrics', {}))}

**异常检测**:
{query_result.get('anomaly_description', '无')}

**数据时间范围**: 
{query_result.get('time_range', '未知')}

**建议操作**:
{chr(10).join('- ' + action for action in template['suggested_actions'])}
        """.strip()
        
        return description
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """格式化指标"""
        if not metrics:
            return "无"
        
        lines = []
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _calculate_confidence(self, query_result: Dict[str, Any]) -> float:
        """计算置信度"""
        # 基于数据质量和异常程度计算
        data_quality = query_result.get("data_quality", 0.8)
        anomaly_severity = query_result.get("anomaly_severity", 0.5)
        
        confidence = (data_quality + anomaly_severity) / 2
        return min(1.0, max(0.0, confidence))
