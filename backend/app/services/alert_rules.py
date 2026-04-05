"""
预警规则引擎 - 实现 6 个业务预警 + 5 个财务风险预警

业务预警规则:
1. 库存预警 - 库存低于安全线
2. 库存为零预警 - 库存为 0
3. 付款逾期预警 - 发票付款逾期
4. 客户流失预警 - 客户 90 天未下单
5. 供应商交货逾期预警 - 采购订单交货逾期
6. 销售订单异常预警 - 订单金额异常波动

财务风险预警:
1. 现金流预警 - 现金流低于安全线
2. 应收账款逾期预警 - 客户应收账款逾期
3. 应付账款风险预警 - 7 天内到期应付
4. 财务比率异常预警 - 流动比率/负债权益比/ROE 异常
5. 预算偏差预警 - 部门预算偏差超过 20%
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from neo4j import Driver

logger = logging.getLogger(__name__)


class AlertRuleEngine:
    """预警规则引擎 - 基于 Neo4j 的风险识别"""

    def __init__(self, neo4j_driver: Driver):
        self.driver = neo4j_driver

    # ==================== 业务预警规则 (6 个) ====================

    def check_inventory_low(self, threshold_days: int = 30) -> List[Dict[str, Any]]:
        """
        规则 1: 库存预警 - 库存低于安全线
        
        基于日均销量计算安全库存，当实际库存低于安全库存时触发预警
        """
        query = """
        MATCH (p:Product)
        WHERE p.stock IS NOT NULL AND p.stock > 0
        
        // 计算日均销量 (过去 30 天)
        OPTIONAL MATCH (p)<-[:CONTAINS]-(s:Sale)
        WHERE s.timestamp >= date() - duration({days: 30})
        WITH p, 
             p.stock as current_stock,
             COALESCE(sum(s.quantity), 0) as total_sales_30d,
             p.threshold as safety_threshold
        
        // 计算安全库存 (日均销量 * 安全天数)
        WITH p, 
             current_stock,
             safety_threshold,
             toFloat(total_sales_30d) / 30.0 as avg_daily_sales,
             toFloat(total_sales_30d) / 30.0 * 30 as calculated_safety_stock
        
        // 触发条件：库存低于安全线
        WHERE current_stock < COALESCE(safety_threshold, calculated_safety_stock)
          AND current_stock > 0
        
        RETURN 
            'INVENTORY_LOW' as alert_type,
            'YELLOW' as severity,
            p.id as product_id,
            p.name as product_name,
            current_stock,
            COALESCE(safety_threshold, calculated_safety_stock) as safety_threshold,
            avg_daily_sales,
            '库存低于安全线，建议补货' as recommendation
        ORDER BY current_stock ASC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_inventory_zero(self) -> List[Dict[str, Any]]:
        """
        规则 2: 库存为零预警 - 库存为 0
        
        当产品库存为 0 且有未完成订单时触发高危预警
        """
        query = """
        MATCH (p:Product)
        WHERE p.stock = 0 OR p.stock IS NULL
        
        // 检查是否有未完成订单
        OPTIONAL MATCH (p)<-[:CONTAINS]-(ol:OrderLine)
        OPTIONAL MATCH (ol)-[:BELONGS_TO]->(o:Order)
        WHERE o.status IN ['PENDING', 'PARTIAL']
        
        WITH p, count(DISTINCT o) as pending_orders
        
        RETURN 
            'INVENTORY_ZERO' as alert_type,
            'RED' as severity,
            p.id as product_id,
            p.name as product_name,
            0 as current_stock,
            pending_orders,
            '库存为 0，' + pending_orders + ' 个订单无法履行' as description,
            '立即紧急补货' as recommendation
        ORDER BY pending_orders DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_payment_overdue(self, overdue_days: int = 1) -> List[Dict[str, Any]]:
        """
        规则 3: 付款逾期预警 - 发票付款逾期
        
        当发票付款状态为逾期且超过到期日时触发预警
        """
        query = """
        MATCH (i:Invoice)
        WHERE i.payment_status = 'OVERDUE' 
          AND i.due_date < date()
        
        // 计算逾期天数
        WITH i, 
             i.due_date as due_date,
             date() as today,
             duration.between(date(i.due_date), date()).days as overdue_days
        
        WHERE overdue_days >= $overdue_days
        
        // 关联供应商
        OPTIONAL MATCH (i)-[:PAYS_TO]->(s:Supplier)
        
        RETURN 
            'PAYMENT_OVERDUE' as alert_type,
            CASE 
                WHEN overdue_days > 30 THEN 'RED'
                WHEN overdue_days > 7 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            i.id as invoice_id,
            i.invoice_number as invoice_number,
            i.amount as amount,
            due_date,
            overdue_days,
            COALESCE(s.vendor_name, '未知供应商') as vendor_name,
            '付款已逾期 ' + overdue_days + ' 天' as description,
            '立即安排付款' as recommendation
        ORDER BY overdue_days DESC, i.amount DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, overdue_days=overdue_days)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_customer_churn(self, inactive_days: int = 90) -> List[Dict[str, Any]]:
        """
        规则 4: 客户流失预警 - 客户 90 天未下单
        
        当活跃客户超过指定天数未下单时触发预警
        """
        query = """
        MATCH (c:Customer)
        WHERE c.status = 'ACTIVE'
        
        // 查找最近一次下单时间
        OPTIONAL MATCH (c)-[:PLACES]->(o:Order)
        WITH c, 
             max(o.order_date) as last_order_date,
             count(o) as total_orders
        
        WHERE last_order_date IS NOT NULL
          AND last_order_date < date() - duration({days: $inactive_days})
        
        // 计算客户价值 (历史订单总额)
        OPTIONAL MATCH (c)-[:PLACES]->(o2:Order)-[:CONTAINS]->(ol:OrderLine)
        WITH c, 
             last_order_date,
             total_orders,
             sum(COALESCE(ol.quantity * ol.unit_price, 0)) as total_revenue
        
        // 计算未下单天数
        WITH c,
             last_order_date,
             total_orders,
             total_revenue,
             duration.between(date(last_order_date), date()).days as days_inactive
        
        RETURN 
            'CUSTOMER_CHURN' as alert_type,
            CASE 
                WHEN total_revenue > 1000000 THEN 'RED'
                WHEN total_revenue > 500000 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            c.id as customer_id,
            c.customer_name as customer_name,
            last_order_date,
            days_inactive,
            total_revenue as historical_revenue,
            '客户已 ' + days_inactive + ' 天未下单，历史贡献 ' + total_revenue + ' 元' as description,
            '客户经理立即联系回访' as recommendation
        ORDER BY total_revenue DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, inactive_days=inactive_days)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_delivery_delay(self, delay_days: int = 3) -> List[Dict[str, Any]]:
        """
        规则 5: 供应商交货逾期预警 - 采购订单交货逾期
        
        当采购订单超过预计交货日期仍未收货时触发预警
        """
        query = """
        MATCH (po:PurchaseOrder)
        WHERE po.status IN ['APPROVED', 'PARTIAL_RECEIVED']
          AND po.expected_delivery_date < date()
        
        // 计算逾期天数
        WITH po,
             date(po.expected_delivery_date) as expected_date,
             duration.between(date(po.expected_delivery_date), date()).days as delay_days
        
        WHERE delay_days >= $delay_days
        
        // 关联供应商
        OPTIONAL MATCH (po)-[:FROM_SUPPLIER]->(s:Supplier)
        
        RETURN 
            'DELIVERY_DELAY' as alert_type,
            CASE 
                WHEN delay_days > 15 THEN 'RED'
                WHEN delay_days > 7 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            po.id as po_id,
            po.po_number as po_number,
            expected_date as expected_delivery_date,
            delay_days,
            COALESCE(s.vendor_name, '未知供应商') as vendor_name,
            po.amount as order_amount,
            '交货已逾期 ' + delay_days + ' 天' as description,
            '联系供应商确认交货时间' as recommendation
        ORDER BY delay_days DESC, po.amount DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, delay_days=delay_days)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_sales_anomaly(self, threshold_percent: float = 0.3) -> List[Dict[str, Any]]:
        """
        规则 6: 销售订单异常预警 - 订单金额异常波动
        
        当客户订单金额相比历史平均水平波动超过阈值时触发预警
        """
        query = """
        MATCH (c:Customer)-[:PLACES]->(o:Order)
        WHERE o.order_date >= date() - duration({days: 7})
        
        // 计算该客户历史平均订单金额 (过去 90 天)
        OPTIONAL MATCH (c)-[:PLACES]->(historical:Order)
        WHERE historical.order_date >= date() - duration({days: 90})
          AND historical.order_date < date() - duration({days: 7})
        
        WITH c, o,
             o.amount as recent_amount,
             COALESCE(avg(historical.amount), 0) as avg_historical_amount
        
        WHERE avg_historical_amount > 0
        
        // 计算波动率
        WITH c, o, recent_amount, avg_historical_amount,
             abs(recent_amount - avg_historical_amount) / avg_historical_amount as variance_rate
        
        WHERE variance_rate > $threshold
        
        RETURN 
            'SALES_ANOMALY' as alert_type,
            CASE 
                WHEN variance_rate > 1.0 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            c.id as customer_id,
            c.customer_name as customer_name,
            o.id as order_id,
            o.order_number as order_number,
            recent_amount,
            avg_historical_amount as historical_avg,
            variance_rate * 100 as variance_percent,
            '订单金额波动 ' + (variance_rate * 100) + '%，远超历史平均' as description,
            '确认订单真实性，防止欺诈' as recommendation
        ORDER BY variance_rate DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, threshold=threshold_percent)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    # ==================== 财务风险预警规则 (5 个) ====================

    def check_cashflow_risk(self) -> List[Dict[str, Any]]:
        """
        财务风险 1: 现金流预警 - 现金流低于安全线
        
        当公司现金流余额低于最低安全阈值时触发高危预警
        """
        query = """
        MATCH (c:Company)-[:HAS_CASHFLOW]->(cf:CashFlow)
        WHERE cf.balance IS NOT NULL
          AND cf.minimum_threshold IS NOT NULL
          AND cf.balance < cf.minimum_threshold
        
        // 计算现金流缺口
        WITH c, cf,
             cf.minimum_threshold - cf.balance as cashflow_gap,
             (cf.balance / cf.minimum_threshold) * 100 as fill_rate
        
        RETURN 
            'CASHFLOW_RISK' as alert_type,
            'RED' as severity,
            c.id as company_id,
            c.company_name as company_name,
            cf.balance as current_balance,
            cf.minimum_threshold as safety_threshold,
            cashflow_gap,
            fill_rate,
            '现金流 ' + cf.balance + ' 元，低于安全线 ' + cf.minimum_threshold + ' 元，缺口 ' + cashflow_gap + ' 元' as description,
            '立即筹集资金或加速回款' as recommendation
        ORDER BY cashflow_gap DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_ar_overdue(self, threshold_amount: int = 100000, threshold_count: int = 5) -> List[Dict[str, Any]]:
        """
        财务风险 2: 应收账款逾期预警 - 客户应收账款逾期
        
        当客户逾期应收账款总额超过阈值或逾期笔数过多时触发预警
        """
        query = """
        MATCH (c:Customer)-[:OWES]->(ar:ARTransaction)
        WHERE ar.due_date < date() 
          AND ar.status = 'UNPAID'
        
        // 汇总逾期金额和笔数
        WITH c, 
             sum(ar.amount) as total_overdue,
             count(ar) as overdue_count,
             max(ar.due_date) as oldest_due_date
        
        WHERE total_overdue > $threshold_amount 
           OR overdue_count > $threshold_count
        
        // 计算平均逾期天数
        WITH c, total_overdue, overdue_count, oldest_due_date,
             duration.between(date(oldest_due_date), date()).days as max_overdue_days
        
        RETURN 
            'AR_OVERDUE_RISK' as alert_type,
            CASE 
                WHEN total_overdue > 500000 OR overdue_count > 10 THEN 'RED'
                WHEN total_overdue > 200000 OR overdue_count > 7 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            c.id as customer_id,
            c.customer_name as customer_name,
            total_overdue,
            overdue_count,
            max_overdue_days,
            '应收账款逾期 ' + total_overdue + ' 元，共 ' + overdue_count + ' 笔，最长逾期 ' + max_overdue_days + ' 天' as description,
            '立即催收或启动法律程序' as recommendation
        ORDER BY total_overdue DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, 
                               threshold_amount=threshold_amount, 
                               threshold_count=threshold_count)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_ap_risk(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        财务风险 3: 应付账款风险预警 - 7 天内到期应付
        
        预测未来指定天数内到期的应付账款，提前预警资金压力
        """
        query = """
        MATCH (s:Supplier)<-[:OWED_BY]-(ap:APTransaction)
        WHERE ap.due_date >= date()
          AND ap.due_date <= date() + duration({days: $days_ahead})
          AND ap.status = 'UNPAID'
        
        // 按供应商汇总
        WITH s,
             sum(ap.amount) as due_in_week,
             count(ap) as invoice_count,
             min(ap.due_date) as earliest_due
        
        WHERE due_in_week > 0
        
        RETURN 
            'AP_RISK' as alert_type,
            'ORANGE' as severity,
            s.id as supplier_id,
            s.vendor_name as supplier_name,
            due_in_week,
            invoice_count,
            earliest_due,
            '未来 ' + $days_ahead + ' 天内需支付 ' + due_in_week + ' 元，共 ' + invoice_count + ' 笔' as description,
            '提前安排资金计划' as recommendation
        ORDER BY due_in_week DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, days_ahead=days_ahead)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_financial_ratio_abnormal(self) -> List[Dict[str, Any]]:
        """
        财务风险 4: 财务比率异常预警 - 关键财务指标异常
        
        监测流动比率、负债权益比、ROE 等关键财务指标，识别财务健康风险
        """
        query = """
        MATCH (c:Company)-[:HAS_FINANCIAL_RATIO]->(r:FinancialRatio)
        WHERE r.current_ratio IS NOT NULL
          AND r.debt_to_equity IS NOT NULL
          AND r.roe IS NOT NULL
        
        // 识别异常指标
        WITH c, r,
             // 流动比率 < 1.0 (短期偿债能力不足)
             CASE WHEN r.current_ratio < 1.0 THEN true ELSE false END as low_current_ratio,
             // 速动比率 < 0.8 (即时偿债能力不足)
             CASE WHEN COALESCE(r.quick_ratio, 1.0) < 0.8 THEN true ELSE false END as low_quick_ratio,
             // 负债权益比 > 2.0 (杠杆过高)
             CASE WHEN r.debt_to_equity > 2.0 THEN true ELSE false END as high_debt_equity,
             // ROE < 5% (盈利能力不足)
             CASE WHEN r.roe < 0.05 THEN true ELSE false END as low_roe,
             // 毛利率 < 15% (利润空间薄)
             CASE WHEN COALESCE(r.gross_margin, 1.0) < 0.15 THEN true ELSE false END as low_margin
        
        // 至少有一个异常指标
        WHERE low_current_ratio OR low_quick_ratio OR high_debt_equity OR low_roe OR low_margin
        
        // 计算异常数量
        WITH c, r, 
             (CASE WHEN low_current_ratio THEN 1 ELSE 0 END +
              CASE WHEN low_quick_ratio THEN 1 ELSE 0 END +
              CASE WHEN high_debt_equity THEN 1 ELSE 0 END +
              CASE WHEN low_roe THEN 1 ELSE 0 END +
              CASE WHEN low_margin THEN 1 ELSE 0 END) as abnormal_count
        
        RETURN 
            'FINANCIAL_RATIO_ABNORMAL' as alert_type,
            CASE 
                WHEN abnormal_count >= 3 THEN 'RED'
                WHEN abnormal_count >= 2 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            c.id as company_id,
            c.company_name as company_name,
            r.current_ratio,
            r.quick_ratio,
            r.debt_to_equity,
            r.roe,
            r.gross_margin,
            abnormal_count,
            '发现 ' + abnormal_count + ' 项财务指标异常' as description,
            '详细分析财务健康状况并制定改善计划' as recommendation
        ORDER BY abnormal_count DESC, r.roe ASC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    def check_budget_variance(self, variance_threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        财务风险 5: 预算偏差预警 - 部门预算偏差超过 20%
        
        当部门实际支出与预算偏差超过阈值时触发预警
        """
        query = """
        MATCH (d:Department)-[:HAS_BUDGET]->(b:Budget)
        MATCH (d)-[:HAS_ACTUAL]->(a:Actual)
        WHERE b.period = a.period
          AND b.amount > 0
          AND b.amount IS NOT NULL
          AND a.amount IS NOT NULL
        
        // 计算预算偏差率
        WITH d, b, a,
             abs(b.amount - a.amount) / b.amount as variance_rate,
             (b.amount - a.amount) as variance_amount
        
        WHERE variance_rate > $threshold
        
        RETURN 
            'BUDGET_VARIANCE' as alert_type,
            CASE 
                WHEN variance_rate > 0.5 THEN 'RED'
                WHEN variance_rate > 0.3 THEN 'ORANGE'
                ELSE 'YELLOW'
            END as severity,
            d.id as department_id,
            d.department_name as department_name,
            b.amount as budget_amount,
            a.amount as actual_amount,
            variance_amount,
            variance_rate * 100 as variance_percent,
            b.period as period,
            '预算 ' + b.amount + ' 元，实际 ' + a.amount + ' 元，偏差 ' + (variance_rate * 100) + '%' as description,
            '分析超支原因并提交说明报告' as recommendation
        ORDER BY variance_rate DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, threshold=variance_threshold)
            alerts = []
            for record in result:
                alerts.append(dict(record))
            return alerts

    # ==================== 综合方法 ====================

    def run_all_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        运行所有预警规则，返回分类结果
        
        Returns:
            包含所有预警规则的字典，按类型分组
        """
        logger.info("Running all alert rules...")
        
        alerts = {
            # 业务预警
            'inventory_low': self.check_inventory_low(),
            'inventory_zero': self.check_inventory_zero(),
            'payment_overdue': self.check_payment_overdue(),
            'customer_churn': self.check_customer_churn(),
            'delivery_delay': self.check_delivery_delay(),
            'sales_anomaly': self.check_sales_anomaly(),
            
            # 财务风险预警
            'cashflow_risk': self.check_cashflow_risk(),
            'ar_overdue_risk': self.check_ar_overdue(),
            'ap_risk': self.check_ap_risk(),
            'financial_ratio_abnormal': self.check_financial_ratio_abnormal(),
            'budget_variance': self.check_budget_variance(),
        }
        
        # 统计预警总数
        total_alerts = sum(len(v) for v in alerts.values())
        logger.info(f"Total alerts generated: {total_alerts}")
        
        return alerts

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        获取预警统计数据
        
        Returns:
            包含各级别预警数量的统计信息
        """
        all_alerts = self.run_all_alerts()
        
        stats = {
            'total': 0,
            'by_severity': {
                'RED': 0,
                'ORANGE': 0,
                'YELLOW': 0,
            },
            'by_type': {},
            'financial_risks': 0,
            'business_alerts': 0,
        }
        
        # 业务预警规则
        business_rules = ['inventory_low', 'inventory_zero', 'payment_overdue', 
                         'customer_churn', 'delivery_delay', 'sales_anomaly']
        
        # 财务风险规则
        financial_rules = ['cashflow_risk', 'ar_overdue_risk', 'ap_risk', 
                          'financial_ratio_abnormal', 'budget_variance']
        
        for rule_name, alerts in all_alerts.items():
            stats['total'] += len(alerts)
            stats['by_type'][rule_name] = len(alerts)
            
            # 统计 severity
            for alert in alerts:
                severity = alert.get('severity', 'YELLOW')
                if severity in stats['by_severity']:
                    stats['by_severity'][severity] += 1
            
            # 分类统计
            if rule_name in financial_rules:
                stats['financial_risks'] += len(alerts)
            elif rule_name in business_rules:
                stats['business_alerts'] += len(alerts)
        
        return stats


# 便捷函数
def create_alert_engine(neo4j_driver: Driver) -> AlertRuleEngine:
    """创建预警规则引擎实例"""
    return AlertRuleEngine(neo4j_driver)
