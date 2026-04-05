"""
智能决策支持模块 - 决策分析服务

实现 15+ Neo4j Cypher 分析查询，支撑 5 大决策场景：
- 库存决策分析 (3 个查询)
- 采购决策分析 (3 个查询)
- 销售决策分析 (3 个查询)
- 财务决策分析 (3 个查询)
- 客户决策分析 (3 个查询)
- 综合分析 (3 个查询)

性能要求：所有查询 <100ms
"""

import logging
from typing import Any, Optional
from datetime import datetime, timedelta
from neo4j import Driver

logger = logging.getLogger(__name__)


class DecisionAnalyticsService:
    """决策分析服务 - 提供 15+ Neo4j 分析查询"""
    
    def __init__(self, neo4j_driver: Driver):
        self.driver = neo4j_driver
    
    # ==================== 库存决策分析 (3 个) ====================
    
    def analyze_inventory_replenishment(self, product_id: Optional[str] = None) -> dict[str, Any]:
        """
        库存补货分析
        
        分析维度:
        - 当前库存水平
        - 销售速度
        - 安全库存
        - 供应商交期
        
        Returns:
            补货建议列表
        """
        cypher = """
        MATCH (p:Product)
        WHERE $product_id IS NULL OR p.id = $product_id
        
        // 计算库存指标
        OPTIONAL MATCH (p)-[:HAS_STOCK]->(s:Stock)
        OPTIONAL MATCH (p)<-[:CONTAINS]-(so:SalesOrder)-[:HAS_STATUS]->(status:OrderStatus)
            WHERE status.status IN ['CONFIRMED', 'PROCESSING']
        
        WITH p, 
             COALESCE(s.quantity, 0) as current_stock,
             COALESCE(p.safety_stock, 0) as safety_stock,
             COALESCE(p.reorder_point, 0) as reorder_point,
             COALESCE(p.lead_time_days, 7) as lead_time,
             COUNT(so) as pending_orders
        
        // 计算日均销量
        OPTIONAL MATCH (p)<-[:CONTAINS]-(sale:Sale)
        WHERE sale.timestamp >= date() - duration({days: 30})
        WITH p, current_stock, safety_stock, reorder_point, lead_time, pending_orders,
             COALESCE(SUM(sale.quantity), 0) / 30.0 as daily_sales
        
        // 计算补货建议
        WITH p, current_stock, safety_stock, reorder_point, lead_time, pending_orders, daily_sales,
             (daily_sales * lead_time) as demand_during_lead_time,
             (current_stock - safety_stock) as buffer
        
        WHERE current_stock < reorder_point OR current_stock < (daily_sales * lead_time * 1.5)
        
        RETURN 
            p.id as product_id,
            p.name as product_name,
            current_stock,
            safety_stock,
            reorder_point,
            daily_sales,
            lead_time,
            pending_orders,
            demand_during_lead_time,
            CASE 
                WHEN current_stock = 0 THEN 'URGENT'
                WHEN current_stock < safety_stock THEN 'HIGH'
                WHEN current_stock < reorder_point THEN 'MEDIUM'
                ELSE 'LOW'
            END as urgency_level,
            (daily_sales * lead_time * 2 - current_stock) as recommended_quantity
        ORDER BY 
            CASE current_stock 
                WHEN 0 THEN 0 
                ELSE 1 
            END,
            daily_sales DESC
        LIMIT 20
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, product_id=product_id)
            records = [dict(record) for record in result]
            
            return {
                "analysis_type": "inventory_replenishment",
                "timestamp": datetime.now().isoformat(),
                "total_products": len(records),
                "recommendations": records
            }
    
    def analyze_slow_moving_inventory(self, days_threshold: int = 90) -> dict[str, Any]:
        """
        呆滞库存分析
        
        识别库龄超过阈值的商品，分析清仓策略
        
        Returns:
            呆滞库存列表和处理建议
        """
        cypher = """
        MATCH (p:Product)
        
        // 获取库存信息
        OPTIONAL MATCH (p)-[:HAS_STOCK]->(s:Stock)
        OPTIONAL MATCH (p)<-[:CONTAINS]-(sale:Sale)
        WHERE sale.timestamp >= date() - duration({days: $days_threshold})
        
        WITH p,
             COALESCE(s.quantity, 0) as stock_qty,
             COALESCE(s.unit_cost, p.cost, 0) as unit_cost,
             COUNT(sale) as recent_sales,
             COALESCE(SUM(sale.quantity), 0) as total_sold
        
        WHERE stock_qty > 0
        
        // 计算库龄和周转率
        WITH p, stock_qty, unit_cost, recent_sales, total_sold,
             CASE 
                WHEN p.last_purchase_date IS NOT NULL 
                THEN duration.between(date(p.last_purchase_date), date()).days
                ELSE 999
             END as age_days,
             CASE 
                WHEN total_sold > 0 THEN stock_qty / (total_sold / $days_threshold)
                ELSE 999
             END as turnover_days
        
        WHERE age_days > $days_threshold OR turnover_days > $days_threshold
        
        RETURN 
            p.id as product_id,
            p.name as product_name,
            p.category as category,
            stock_qty,
            unit_cost,
            (stock_qty * unit_cost) as inventory_value,
            recent_sales,
            total_sold,
            age_days,
            turnover_days,
            CASE 
                WHEN age_days > 180 THEN 'CLEAR_IMMEDIATELY'
                WHEN age_days > 120 THEN 'DISCOUNT_50'
                WHEN age_days > 90 THEN 'DISCOUNT_30'
                ELSE 'MONITOR'
            END as action_recommendation
        ORDER BY inventory_value DESC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, days_threshold=days_threshold)
            records = [dict(record) for record in result]
            
            total_value = sum(r.get('inventory_value', 0) for r in records)
            
            return {
                "analysis_type": "slow_moving_inventory",
                "timestamp": datetime.now().isoformat(),
                "threshold_days": days_threshold,
                "total_items": len(records),
                "total_value": total_value,
                "recommendations": records
            }
    
    def analyze_inventory_distribution(self) -> dict[str, Any]:
        """
        库存分布分析
        
        分析多仓库库存分布，识别调拨机会
        
        Returns:
            库存分布和调拨建议
        """
        cypher = """
        MATCH (w:Warehouse)
        MATCH (w)-[:STORES]->(s:Stock)-[:BELONGS_TO]->(p:Product)
        
        WITH p, w, s.quantity as stock_qty
        
        // 计算每个产品的总库存和各仓库分布
        WITH p, 
             COLLECT({warehouse: w.name, quantity: stock_qty, location: w.location}) as distribution,
             SUM(stock_qty) as total_stock
        
        // 计算需求（基于各仓库区域的销售）
        OPTIONAL MATCH (p)<-[:CONTAINS]-(sale:Sale)-[:FROM_WAREHOUSE]->(w2)
        WHERE sale.timestamp >= date() - duration({days: 30})
        WITH p, distribution, total_stock,
             COUNT(sale) as demand_count
        
        WHERE total_stock > 0
        
        RETURN 
            p.id as product_id,
            p.name as product_name,
            distribution,
            total_stock,
            demand_count,
            CASE 
                WHEN SIZE(distribution) > 1 AND 
                     REDUCE(max = 0, d IN distribution | CASE WHEN d.quantity > max THEN d.quantity ELSE max END) / 
                     REDUCE(min = total_stock, d IN distribution | CASE WHEN d.quantity < min THEN d.quantity ELSE min END) > 3
                THEN 'REBALANCE_NEEDED'
                ELSE 'BALANCED'
            END as balance_status
        ORDER BY total_stock DESC
        LIMIT 30
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            imbalance_count = sum(1 for r in records if r.get('balance_status') == 'REBALANCE_NEEDED')
            
            return {
                "analysis_type": "inventory_distribution",
                "timestamp": datetime.now().isoformat(),
                "total_products": len(records),
                "imbalance_count": imbalance_count,
                "recommendations": records
            }
    
    # ==================== 采购决策分析 (3 个) ====================
    
    def analyze_supplier_performance(self, supplier_id: Optional[str] = None) -> dict[str, Any]:
        """
        供应商绩效分析
        
        评估供应商综合表现，支持供应商选择决策
        
        Returns:
            供应商绩效评分和排名
        """
        cypher = """
        MATCH (s:Supplier)
        WHERE $supplier_id IS NULL OR s.id = $supplier_id
        
        // 获取采购订单
        OPTIONAL MATCH (s)<-[:SUPPLIED_BY]-(po:PurchaseOrder)
        OPTIONAL MATCH (po)-[:HAS_STATUS]->(po_status:POStatus)
        
        // 获取发票和付款
        OPTIONAL MATCH (s)<-[:SUPPLIES_TO]-(invoice:Invoice)
        
        WITH s,
             COUNT(DISTINCT po) as total_orders,
             SUM(CASE WHEN po_status.status = 'DELIVERED' THEN 1 ELSE 0 END) as delivered_orders,
             SUM(CASE WHEN po_status.status = 'ON_TIME' THEN 1 ELSE 0 END) as on_time_orders,
             COUNT(DISTINCT invoice) as total_invoices,
             SUM(CASE WHEN invoice.status = 'PAID' THEN invoice.amount ELSE 0 END) as paid_amount,
             SUM(CASE WHEN invoice.status = 'OVERDUE' THEN invoice.amount ELSE 0 END) as overdue_amount
        
        WHERE total_orders > 0
        
        // 计算绩效指标
        WITH s, total_orders, delivered_orders, on_time_orders, total_invoices, paid_amount, overdue_amount,
             CASE WHEN total_orders > 0 THEN delivered_orders * 1.0 / total_orders ELSE 0 END as delivery_rate,
             CASE WHEN on_time_orders > 0 THEN on_time_orders * 1.0 / delivered_orders ELSE 0 END as on_time_rate,
             CASE WHEN paid_amount + overdue_amount > 0 THEN paid_amount * 1.0 / (paid_amount + overdue_amount) ELSE 0 END as payment_compliance
        
        // 计算综合评分
        WITH s, total_orders, delivery_rate, on_time_rate, payment_compliance,
             (delivery_rate * 0.4 + on_time_rate * 0.4 + payment_compliance * 0.2) * 100 as performance_score
        
        RETURN 
            s.id as supplier_id,
            s.vendor_name as supplier_name,
            s.category as category,
            total_orders,
            ROUND(delivery_rate * 100, 2) as delivery_rate_percent,
            ROUND(on_time_rate * 100, 2) as on_time_rate_percent,
            paid_amount as total_paid,
            overdue_amount as overdue_amount,
            ROUND(performance_score, 2) as performance_score,
            CASE 
                WHEN performance_score >= 90 THEN 'EXCELLENT'
                WHEN performance_score >= 75 THEN 'GOOD'
                WHEN performance_score >= 60 THEN 'AVERAGE'
                ELSE 'POOR'
            END as rating
        ORDER BY performance_score DESC
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, supplier_id=supplier_id)
            records = [dict(record) for record in result]
            
            return {
                "analysis_type": "supplier_performance",
                "timestamp": datetime.now().isoformat(),
                "total_suppliers": len(records),
                "excellent_count": sum(1 for r in records if r.get('rating') == 'EXCELLENT'),
                "poor_count": sum(1 for r in records if r.get('rating') == 'POOR'),
                "suppliers": records
            }
    
    def analyze_procurement_timing(self, product_id: Optional[str] = None) -> dict[str, Any]:
        """
        采购时机分析
        
        基于价格趋势和需求预测，建议最佳采购时间
        
        Returns:
            采购时机建议
        """
        cypher = """
        MATCH (p:Product)
        WHERE $product_id IS NULL OR p.id = $product_id
        
        // 获取历史采购价格
        OPTIONAL MATCH (p)<-[:CONTAINS]-(po:PurchaseOrder)-[:HAS_PRICE]->(price:Price)
        WHERE price.timestamp >= date() - duration({months: 6})
        
        // 获取当前库存和需求
        OPTIONAL MATCH (p)-[:HAS_STOCK]->(s:Stock)
        OPTIONAL MATCH (p)<-[:CONTAINS]-(so:SalesOrder)
        WHERE so.timestamp >= date() - duration({days: 30})
        
        WITH p,
             COALESCE(s.quantity, 0) as current_stock,
             COALESCE(p.reorder_point, 0) as reorder_point,
             COUNT(DISTINCT po) as price_points,
             AVG(price.amount) as avg_price,
             MIN(price.amount) as min_price,
             MAX(price.amount) as max_price,
             COUNT(DISTINCT so) as monthly_demand
        
        WHERE price_points > 0
        
        // 计算价格趋势和采购建议
        WITH p, current_stock, reorder_point, avg_price, min_price, max_price, monthly_demand,
             CASE 
                WHEN avg_price < min_price * 1.1 THEN 'GOOD_TIME'
                WHEN avg_price > max_price * 0.9 THEN 'WAIT'
                ELSE 'NEUTRAL'
             END as timing_recommendation
        
        RETURN 
            p.id as product_id,
            p.name as product_name,
            current_stock,
            reorder_point,
            ROUND(avg_price, 2) as avg_price,
            ROUND(min_price, 2) as min_price,
            ROUND(max_price, 2) as max_price,
            monthly_demand,
            timing_recommendation,
            CASE 
                WHEN current_stock < reorder_point AND timing_recommendation = 'GOOD_TIME' THEN 'BUY_NOW'
                WHEN current_stock < reorder_point THEN 'BUY_URGENT'
                WHEN timing_recommendation = 'WAIT' THEN 'WAIT_BETTER_PRICE'
                ELSE 'MONITOR'
            END as action
        ORDER BY 
            CASE current_stock < reorder_point WHEN true THEN 0 ELSE 1 END,
            timing_recommendation
        LIMIT 30
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, product_id=product_id)
            records = [dict(record) for record in result]
            
            return {
                "analysis_type": "procurement_timing",
                "timestamp": datetime.now().isoformat(),
                "total_products": len(records),
                "buy_now_count": sum(1 for r in records if r.get('action') == 'BUY_NOW'),
                "wait_count": sum(1 for r in records if r.get('action') == 'WAIT_BETTER_PRICE'),
                "recommendations": records
            }
    
    def analyze_supplier_risk(self) -> dict[str, Any]:
        """
        供应商风险分析
        
        评估供应商供应风险，支持多元化采购决策
        
        Returns:
            供应商风险评估
        """
        cypher = """
        MATCH (s:Supplier)
        
        // 获取供应商依赖度
        OPTIONAL MATCH (s)<-[:SUPPLIED_BY]-(po:PurchaseOrder)
        WHERE po.timestamp >= date() - duration({months: 3})
        
        // 获取替代供应商
        OPTIONAL MATCH (s)<-[:SUPPLIES]-(p:Product)-[:SUPPLIED_BY]-(other:Supplier)
        WHERE other <> s
        
        WITH s,
             COUNT(DISTINCT po) as order_count,
             COUNT(DISTINCT other) as alternative_suppliers,
             COUNT(DISTINCT p) as supplied_products
        
        WHERE order_count > 0
        
        // 计算风险评分
        WITH s, order_count, alternative_suppliers, supplied_products,
             CASE 
                WHEN alternative_suppliers = 0 THEN 100
                WHEN alternative_suppliers = 1 THEN 60
                WHEN alternative_suppliers = 2 THEN 30
                ELSE 10
             END as dependency_risk,
             CASE 
                WHEN supplied_products > 10 THEN 50
                WHEN supplied_products > 5 THEN 30
                ELSE 10
             END as concentration_risk
        
        WITH s, order_count, alternative_suppliers, supplied_products,
             (dependency_risk + concentration_risk) / 2 as risk_score
        
        RETURN 
            s.id as supplier_id,
            s.vendor_name as supplier_name,
            order_count,
            alternative_suppliers,
            supplied_products,
            ROUND(risk_score, 2) as risk_score,
            CASE 
                WHEN risk_score >= 70 THEN 'HIGH_RISK'
                WHEN risk_score >= 40 THEN 'MEDIUM_RISK'
                ELSE 'LOW_RISK'
            END as risk_level,
            CASE 
                WHEN alternative_suppliers = 0 THEN 'FIND_ALTERNATIVE'
                WHEN risk_score >= 70 THEN 'REDUCE_DEPENDENCY'
                ELSE 'MONITOR'
            END as recommendation
        ORDER BY risk_score DESC
        LIMIT 30
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            high_risk_count = sum(1 for r in records if r.get('risk_level') == 'HIGH_RISK')
            
            return {
                "analysis_type": "supplier_risk",
                "timestamp": datetime.now().isoformat(),
                "total_suppliers": len(records),
                "high_risk_count": high_risk_count,
                "suppliers": records
            }
    
    # ==================== 销售决策分析 (3 个) ====================
    
    def analyze_pricing_elasticity(self, product_id: Optional[str] = None) -> dict[str, Any]:
        """
        价格弹性分析
        
        分析产品价格敏感度，支持定价决策
        
        Returns:
            价格弹性系数和建议
        """
        cypher = """
        MATCH (p:Product)
        WHERE $product_id IS NULL OR p.id = $product_id
        
        // 获取历史销售和价格变化
        OPTIONAL MATCH (p)<-[:CONTAINS]-(sale:Sale)-[:HAS_PRICE]->(price:Price)
        WHERE sale.timestamp >= date() - duration({months: 6})
        
        WITH p,
             COUNT(DISTINCT sale) as sale_count,
             AVG(price.amount) as avg_price,
             AVG(sale.quantity) as avg_quantity,
             STDEV(price.amount) as price_stddev,
             STDEV(sale.quantity) as quantity_stddev
        
        WHERE sale_count >= 10 AND price_stddev > 0
        
        // 计算价格弹性
        WITH p, avg_price, avg_quantity, price_stddev, quantity_stddev, sale_count,
             CASE 
                WHEN price_stddev > 0 THEN (quantity_stddev / avg_quantity) / (price_stddev / avg_price)
                ELSE 0
             END as elasticity
        
        RETURN 
            p.id as product_id,
            p.name as product_name,
            p.category as category,
            ROUND(avg_price, 2) as avg_price,
            ROUND(avg_quantity, 2) as avg_quantity,
            sale_count,
            ROUND(elasticity, 2) as price_elasticity,
            CASE 
                WHEN elasticity < -1.5 THEN 'HIGHLY_ELASTIC'
                WHEN elasticity < -1.0 THEN 'ELASTIC'
                WHEN elasticity < -0.5 THEN 'INELASTIC'
                ELSE 'VERY_INELASTIC'
            END as elasticity_category,
            CASE 
                WHEN elasticity < -1.5 THEN 'REDUCE_PRICE'
                WHEN elasticity < -1.0 THEN 'SLIGHT_REDUCE'
                WHEN elasticity < -0.5 THEN 'MAINTAIN'
                ELSE 'INCREASE_PRICE'
            END as pricing_recommendation
        ORDER BY elasticity ASC
        LIMIT 30
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, product_id=product_id)
            records = [dict(record) for record in result]
            
            return {
                "analysis_type": "pricing_elasticity",
                "timestamp": datetime.now().isoformat(),
                "total_products": len(records),
                "elastic_count": sum(1 for r in records if r.get('elasticity_category') in ['ELASTIC', 'HIGHLY_ELASTIC']),
                "recommendations": records
            }
    
    def analyze_promotion_effectiveness(self, days_lookback: int = 90) -> dict[str, Any]:
        """
        促销活动效果分析
        
        评估历史促销活动效果，支持促销决策
        
        Returns:
            促销活动效果统计
        """
        cypher = """
        MATCH (promo:Promotion)
        WHERE promo.start_date >= date() - duration({days: $days_lookback})
        
        // 获取促销期间销售
        OPTIONAL MATCH (promo)-[:APPLIES_TO]->(p:Product)<-[:CONTAINS]-(sale:Sale)
        WHERE sale.timestamp >= promo.start_date AND sale.timestamp <= promo.end_date
        
        // 获取非促销期间销售（对比基线）
        OPTIONAL MATCH (p)<-[:CONTAINS]-(baseline_sale:Sale)
        WHERE baseline_sale.timestamp >= promo.start_date - duration({days: 30})
          AND baseline_sale.timestamp < promo.start_date
        
        WITH promo,
             COUNT(DISTINCT sale) as promo_sales,
             SUM(COALESCE(sale.amount, 0)) as promo_revenue,
             COUNT(DISTINCT baseline_sale) as baseline_sales,
             SUM(COALESCE(baseline_sale.amount, 0)) as baseline_revenue,
             promo.cost as promo_cost
        
        WHERE promo_sales > 0
        
        // 计算促销效果
        WITH promo, promo_sales, promo_revenue, baseline_sales, baseline_revenue, COALESCE(promo_cost, 0) as promo_cost,
             CASE WHEN baseline_revenue > 0 
                  THEN (promo_revenue - baseline_revenue) / baseline_revenue * 100 
                  ELSE 0 
             END as revenue_lift_percent,
             CASE WHEN baseline_sales > 0 
                  THEN (promo_sales - baseline_sales) * 1.0 / baseline_sales * 100 
                  ELSE 0 
             END as sales_lift_percent
        
        WITH promo, promo_sales, promo_revenue, baseline_sales, baseline_revenue, promo_cost,
             revenue_lift_percent, sales_lift_percent,
             (promo_revenue - baseline_revenue - promo_cost) as incremental_profit
        
        RETURN 
            promo.id as promotion_id,
            promo.name as promotion_name,
            promo.type as promotion_type,
            promo_sales,
            ROUND(promo_revenue, 2) as promo_revenue,
            baseline_sales,
            ROUND(baseline_revenue, 2) as baseline_revenue,
            ROUND(revenue_lift_percent, 2) as revenue_lift_percent,
            ROUND(sales_lift_percent, 2) as sales_lift_percent,
            promo_cost,
            ROUND(incremental_profit, 2) as incremental_profit,
            CASE 
                WHEN incremental_profit > 0 THEN 'SUCCESS'
                ELSE 'FAILED'
            END as effectiveness
        ORDER BY incremental_profit DESC
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, days_lookback=days_lookback)
            records = [dict(record) for record in result]
            
            success_count = sum(1 for r in records if r.get('effectiveness') == 'SUCCESS')
            total_roi = (
                sum(r.get('incremental_profit', 0) for r in records) / 
                max(sum(r.get('promo_cost', 0) for r in records), 1) * 100
            )
            
            return {
                "analysis_type": "promotion_effectiveness",
                "timestamp": datetime.now().isoformat(),
                "total_promotions": len(records),
                "success_count": success_count,
                "success_rate": round(success_count / max(len(records), 1) * 100, 2),
                "total_roi": round(total_roi, 2),
                "promotions": records
            }
    
    def analyze_customer_segmentation(self) -> dict[str, Any]:
        """
        客户细分分析
        
        基于 RFM 模型进行客户细分，支持差异化营销策略
        
        Returns:
            客户细分结果
        """
        cypher = """
        MATCH (c:Customer)
        
        // 获取客户购买行为
        OPTIONAL MATCH (c)-[:PLACES]->(o:Order)-[:HAS_STATUS]->(status:OrderStatus)
        WHERE status.status IN ['COMPLETED', 'DELIVERED']
        OPTIONAL MATCH (o)-[:HAS_AMOUNT]->(amt:Amount)
        
        WITH c,
             COUNT(DISTINCT o) as total_orders,
             COALESCE(SUM(amt.amount), 0) as total_revenue,
             MAX(o.timestamp) as last_order_date
        
        WHERE total_orders > 0
        
        // 计算 RFM 分数
        WITH c, total_orders, total_revenue, last_order_date,
             duration.between(last_order_date, date()).days as recency_days,
             total_orders as frequency,
             total_revenue / total_orders as monetary
        
        // RFM 评分 (1-5 分)
        WITH c, total_orders, total_revenue,
             CASE 
                WHEN recency_days <= 30 THEN 5
                WHEN recency_days <= 60 THEN 4
                WHEN recency_days <= 90 THEN 3
                WHEN recency_days <= 180 THEN 2
                ELSE 1
             END as r_score,
             CASE 
                WHEN total_orders >= 20 THEN 5
                WHEN total_orders >= 10 THEN 4
                WHEN total_orders >= 5 THEN 3
                WHEN total_orders >= 2 THEN 2
                ELSE 1
             END as f_score,
             CASE 
                WHEN monetary >= 10000 THEN 5
                WHEN monetary >= 5000 THEN 4
                WHEN monetary >= 2000 THEN 3
                WHEN monetary >= 1000 THEN 2
                ELSE 1
             END as m_score
        
        WITH c, total_orders, total_revenue, r_score, f_score, m_score,
             (r_score + f_score + m_score) as rfm_total
        
        RETURN 
            c.id as customer_id,
            c.customer_name as customer_name,
            c.industry as industry,
            total_orders,
            ROUND(total_revenue, 2) as total_revenue,
            r_score as recency_score,
            f_score as frequency_score,
            m_score as monetary_score,
            rfm_total,
            CASE 
                WHEN rfm_total >= 13 THEN 'CHAMPIONS'
                WHEN rfm_total >= 10 THEN 'LOYAL'
                WHEN rfm_total >= 7 THEN 'POTENTIAL'
                WHEN rfm_total >= 4 THEN 'AT_RISK'
                ELSE 'LOST'
            END as segment
        ORDER BY rfm_total DESC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            # 统计各细分客户数
            segments = {}
            for r in records:
                seg = r.get('segment', 'UNKNOWN')
                segments[seg] = segments.get(seg, 0) + 1
            
            return {
                "analysis_type": "customer_segmentation",
                "timestamp": datetime.now().isoformat(),
                "total_customers": len(records),
                "segment_distribution": segments,
                "customers": records
            }
    
    # ==================== 财务决策分析 (3 个) ====================
    
    def analyze_cash_flow_forecast(self, days_forecast: int = 30) -> dict[str, Any]:
        """
        现金流预测分析
        
        预测未来现金流状况，支持资金调配决策
        
        Returns:
            现金流预测和预警
        """
        cypher = """
        MATCH (c:Company)
        
        // 获取应收账款
        OPTIONAL MATCH (c)<-[:OWED_BY]-(ar:ARTransaction)
        WHERE ar.status = 'UNPAID' AND ar.due_date <= date() + duration({days: $days_forecast})
        
        // 获取应付账款
        OPTIONAL MATCH (c)-[:OWES]->(ap:APTransaction)
        WHERE ap.status = 'UNPAID' AND ap.due_date <= date() + duration({days: $days_forecast})
        
        // 获取当前现金
        OPTIONAL MATCH (c)-[:HAS_CASHFLOW]->(cf:CashFlow)
        
        WITH c,
             COALESCE(SUM(ar.amount), 0) as expected_inflow,
             COALESCE(SUM(ap.amount), 0) as expected_outflow,
             COALESCE(cf.balance, 0) as current_cash,
             COALESCE(cf.minimum_threshold, 0) as minimum_threshold
        
        // 按周分组
        WITH c, expected_inflow, expected_outflow, current_cash, minimum_threshold,
             (expected_inflow - expected_outflow) as net_cash_flow,
             (current_cash + expected_inflow - expected_outflow) as projected_cash
        
        RETURN 
            c.id as company_id,
            c.name as company_name,
            current_cash,
            expected_inflow,
            expected_outflow,
            net_cash_flow,
            projected_cash,
            minimum_threshold,
            CASE 
                WHEN projected_cash < minimum_threshold THEN 'CRITICAL'
                WHEN projected_cash < minimum_threshold * 1.5 THEN 'WARNING'
                ELSE 'HEALTHY'
            END as cash_status,
            CASE 
                WHEN projected_cash < minimum_threshold THEN 'IMMEDIATE_ACTION_NEEDED'
                WHEN projected_cash < minimum_threshold * 1.5 THEN 'MONITOR_CLOSELY'
                ELSE 'NO_ACTION'
            END as recommendation
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, days_forecast=days_forecast)
            records = [dict(record) for record in result]
            
            critical_count = sum(1 for r in records if r.get('cash_status') == 'CRITICAL')
            warning_count = sum(1 for r in records if r.get('cash_status') == 'WARNING')
            
            return {
                "analysis_type": "cash_flow_forecast",
                "timestamp": datetime.now().isoformat(),
                "forecast_days": days_forecast,
                "critical_count": critical_count,
                "warning_count": warning_count,
                "companies": records
            }
    
    def analyze_payment_priority(self) -> dict[str, Any]:
        """
        付款优先级分析
        
        在资金有限情况下，建议付款优先级
        
        Returns:
            应付款优先级排序
        """
        cypher = """
        MATCH (s:Supplier)<-[:OWED_BY]-(ap:APTransaction)
        WHERE ap.status = 'UNPAID'
        
        // 获取供应商重要性
        OPTIONAL MATCH (s)<-[:SUPPLIED_BY]-(po:PurchaseOrder)
        WHERE po.timestamp >= date() - duration({months: 6})
        
        // 获取现金折扣
        WITH s, ap,
             COUNT(DISTINCT po) as recent_orders,
             CASE 
                WHEN ap.due_date < date() THEN 1
                WHEN ap.due_date <= date() + duration({days: 7}) THEN 2
                WHEN ap.due_date <= date() + duration({days: 30}) THEN 3
                ELSE 4
             END as urgency_level,
             CASE 
                WHEN ap.discount_amount > 0 THEN 1
                ELSE 2
             END as discount_priority
        
        WITH s, ap, recent_orders, urgency_level, discount_priority,
             CASE 
                WHEN recent_orders >= 20 THEN 1
                WHEN recent_orders >= 10 THEN 2
                ELSE 3
             END as supplier_importance
        
        // 计算综合优先级分数
        WITH s, ap, recent_orders,
             (urgency_level * 0.4 + discount_priority * 0.3 + supplier_importance * 0.3) as priority_score
        
        RETURN 
            ap.id as ap_id,
            ap.amount as amount,
            ap.due_date as due_date,
            s.id as supplier_id,
            s.vendor_name as supplier_name,
            recent_orders,
            urgency_level,
            discount_priority,
            supplier_importance,
            ROUND(priority_score, 2) as priority_score,
            CASE 
                WHEN priority_score < 1.5 THEN 'HIGHEST'
                WHEN priority_score < 2.0 THEN 'HIGH'
                WHEN priority_score < 2.5 THEN 'MEDIUM'
                ELSE 'LOW'
            END as priority_level
        ORDER BY priority_score ASC, due_date ASC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            highest_priority = sum(1 for r in records if r.get('priority_level') == 'HIGHEST')
            total_amount = sum(r.get('amount', 0) for r in records)
            
            return {
                "analysis_type": "payment_priority",
                "timestamp": datetime.now().isoformat(),
                "total_payables": len(records),
                "highest_priority_count": highest_priority,
                "total_amount": total_amount,
                "payables": records
            }
    
    def analyze_ar_aging(self) -> dict[str, Any]:
        """
        应收账款账龄分析
        
        分析应收账款账龄，支持催收决策
        
        Returns:
            账龄分析和催收建议
        """
        cypher = """
        MATCH (c:Customer)-[:OWES]->(ar:ARTransaction)
        WHERE ar.status = 'UNPAID'
        
        WITH c, ar,
             duration.between(ar.due_date, date()).days as days_overdue
        
        // 按账龄分组
        WITH c, ar, days_overdue,
             CASE 
                WHEN days_overdue < 0 THEN 'NOT_DUE'
                WHEN days_overdue <= 30 THEN '1-30_DAYS'
                WHEN days_overdue <= 60 THEN '31-60_DAYS'
                WHEN days_overdue <= 90 THEN '61-90_DAYS'
                ELSE 'OVER_90_DAYS'
             END as aging_bucket
        
        // 汇总各账龄段
        WITH c, aging_bucket, SUM(ar.amount) as amount_in_bucket, COUNT(ar) as count_in_bucket
        
        RETURN 
            c.id as customer_id,
            c.customer_name as customer_name,
            aging_bucket,
            ROUND(amount_in_bucket, 2) as amount,
            count_in_bucket as invoice_count,
            CASE aging_bucket
                WHEN 'NOT_DUE' THEN 'MONITOR'
                WHEN '1-30_DAYS' THEN 'REMIND'
                WHEN '31-60_DAYS' THEN 'FOLLOW_UP'
                WHEN '61-90_DAYS' THEN 'INTENSIVE_COLLECTION'
                ELSE 'LEGAL_ACTION'
            END as collection_action
        ORDER BY 
            CASE aging_bucket
                WHEN 'OVER_90_DAYS' THEN 0
                WHEN '61-90_DAYS' THEN 1
                WHEN '31-60_DAYS' THEN 2
                WHEN '1-30_DAYS' THEN 3
                ELSE 4
            END,
            amount DESC
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            # 按账龄段汇总
            aging_summary = {}
            for r in records:
                bucket = r.get('aging_bucket', 'UNKNOWN')
                if bucket not in aging_summary:
                    aging_summary[bucket] = {'amount': 0, 'count': 0}
                aging_summary[bucket]['amount'] += r.get('amount', 0)
                aging_summary[bucket]['count'] += r.get('invoice_count', 0)
            
            return {
                "analysis_type": "ar_aging",
                "timestamp": datetime.now().isoformat(),
                "total_customers": len(set(r.get('customer_id') for r in records)),
                "aging_summary": aging_summary,
                "customers": records
            }
    
    # ==================== 客户决策分析 (3 个) ====================
    
    def analyze_customer_lifetime_value(self) -> dict[str, Any]:
        """
        客户终身价值分析
        
        预测客户终身价值，支持客户获取和维护决策
        
        Returns:
            客户 LTV 排名和分群
        """
        cypher = """
        MATCH (c:Customer)
        
        // 获取历史购买数据
        OPTIONAL MATCH (c)-[:PLACES]->(o:Order)-[:HAS_STATUS]->(status:OrderStatus)
        WHERE status.status IN ['COMPLETED', 'DELIVERED']
        OPTIONAL MATCH (o)-[:HAS_AMOUNT]->(amt:Amount)
        
        WITH c,
             COUNT(DISTINCT o) as total_orders,
             COALESCE(SUM(amt.amount), 0) as total_revenue,
             MIN(o.timestamp) as first_order_date,
             MAX(o.timestamp) as last_order_date
        
        WHERE total_orders > 0
        
        // 计算客户价值指标
        WITH c, total_orders, total_revenue, first_order_date, last_order_date,
             duration.between(first_order_date, last_order_date).days as customer_lifespan_days,
             total_revenue / total_orders as avg_order_value,
             CASE WHEN customer_lifespan_days > 0 
                  THEN total_orders * 365.0 / customer_lifespan_days 
                  ELSE total_orders 
             END as annual_frequency
        
        // 预测 LTV (假设平均客户生命周期 3 年)
        WITH c, total_orders, total_revenue, avg_order_value, annual_frequency,
             avg_order_value * annual_frequency * 3 as predicted_ltv,
             total_revenue / GREATEST(duration.between(first_order_date, date()).days / 365.0, 1) as annual_revenue
        
        RETURN 
            c.id as customer_id,
            c.customer_name as customer_name,
            c.industry as industry,
            total_orders,
            ROUND(total_revenue, 2) as total_revenue,
            ROUND(avg_order_value, 2) as avg_order_value,
            ROUND(annual_frequency, 2) as annual_frequency,
            ROUND(predicted_ltv, 2) as predicted_ltv,
            ROUND(annual_revenue, 2) as annual_revenue,
            CASE 
                WHEN predicted_ltv >= 100000 THEN 'PLATINUM'
                WHEN predicted_ltv >= 50000 THEN 'GOLD'
                WHEN predicted_ltv >= 20000 THEN 'SILVER'
                ELSE 'BRONZE'
            END as ltv_tier
        ORDER BY predicted_ltv DESC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            # 统计各层级客户数
            tier_distribution = {}
            for r in records:
                tier = r.get('ltv_tier', 'UNKNOWN')
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            
            return {
                "analysis_type": "customer_lifetime_value",
                "timestamp": datetime.now().isoformat(),
                "total_customers": len(records),
                "tier_distribution": tier_distribution,
                "top_ltv": records[:10] if len(records) > 10 else records,
                "customers": records
            }
    
    def analyze_churn_risk(self) -> dict[str, Any]:
        """
        客户流失风险分析
        
        识别有流失风险的客户，支持客户保留决策
        
        Returns:
            流失风险客户列表
        """
        cypher = """
        MATCH (c:Customer)
        
        // 获取购买历史
        OPTIONAL MATCH (c)-[:PLACES]->(o:Order)-[:HAS_STATUS]->(status:OrderStatus)
        WHERE status.status IN ['COMPLETED', 'DELIVERED']
        
        WITH c,
             COUNT(DISTINCT o) as total_orders,
             MAX(o.timestamp) as last_order_date,
             MIN(o.timestamp) as first_order_date
        
        WHERE total_orders >= 2
        
        // 计算流失风险指标
        WITH c, total_orders, last_order_date, first_order_date,
             duration.between(last_order_date, date()).days as days_since_last_order,
             duration.between(first_order_date, last_order_date).days as customer_age_days,
             CASE WHEN total_orders > 1 
                  THEN duration.between(first_order_date, last_order_date).days / (total_orders - 1) 
                  ELSE 90 
             END as avg_purchase_interval
        
        // 计算流失概率
        WITH c, total_orders, last_order_date, days_since_last_order, avg_purchase_interval,
             CASE 
                WHEN days_since_last_order > avg_purchase_interval * 3 THEN 0.9
                WHEN days_since_last_order > avg_purchase_interval * 2 THEN 0.7
                WHEN days_since_last_order > avg_purchase_interval * 1.5 THEN 0.5
                WHEN days_since_last_order > avg_purchase_interval THEN 0.3
                ELSE 0.1
             END as churn_probability
        
        WHERE churn_probability >= 0.5
        
        RETURN 
            c.id as customer_id,
            c.customer_name as customer_name,
            total_orders,
            last_order_date,
            days_since_last_order,
            ROUND(avg_purchase_interval, 0) as avg_purchase_interval,
            ROUND(churn_probability, 2) as churn_probability,
            CASE 
                WHEN churn_probability >= 0.9 THEN 'CRITICAL'
                WHEN churn_probability >= 0.7 THEN 'HIGH'
                ELSE 'MEDIUM'
            END as churn_risk_level,
            CASE 
                WHEN churn_probability >= 0.9 THEN 'IMMEDIATE_INTERVENTION'
                WHEN churn_probability >= 0.7 THEN 'PROACTIVE_OUTREACH'
                ELSE 'MONITOR'
            END as retention_action
        ORDER BY churn_probability DESC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            critical_count = sum(1 for r in records if r.get('churn_risk_level') == 'CRITICAL')
            high_count = sum(1 for r in records if r.get('churn_risk_level') == 'HIGH')
            
            return {
                "analysis_type": "churn_risk",
                "timestamp": datetime.now().isoformat(),
                "total_at_risk": len(records),
                "critical_count": critical_count,
                "high_count": high_count,
                "customers": records
            }
    
    def analyze_customer_acquisition_cost(self) -> dict[str, Any]:
        """
        客户获取成本分析
        
        分析不同渠道的客户获取成本，支持营销预算分配决策
        
        Returns:
            渠道 CAC 分析
        """
        cypher = """
        MATCH (c:Customer)
        WHERE c.acquisition_channel IS NOT NULL
        
        // 获取客户价值
        OPTIONAL MATCH (c)-[:PLACES]->(o:Order)-[:HAS_STATUS]->(status:OrderStatus)
        WHERE status.status IN ['COMPLETED', 'DELIVERED']
        OPTIONAL MATCH (o)-[:HAS_AMOUNT]->(amt:Amount)
        
        WITH c,
             c.acquisition_channel as channel,
             c.acquisition_cost as cac,
             COUNT(DISTINCT o) as total_orders,
             COALESCE(SUM(amt.amount), 0) as total_revenue
        
        // 按渠道汇总
        WITH channel,
             COUNT(c) as customer_count,
             SUM(COALESCE(cac, 0)) as total_cac,
             SUM(total_revenue) as total_revenue,
             SUM(total_orders) as total_orders
        
        WITH channel, customer_count, total_cac, total_revenue, total_orders,
             CASE WHEN customer_count > 0 THEN total_cac / customer_count ELSE 0 END as avg_cac,
             CASE WHEN total_orders > 0 THEN total_revenue / total_orders ELSE 0 END as avg_order_value,
             CASE WHEN total_cac > 0 THEN total_revenue / total_cac ELSE 0 END as cac_roi
        
        RETURN 
            channel,
            customer_count,
            ROUND(total_cac, 2) as total_cac,
            ROUND(avg_cac, 2) as avg_cac,
            ROUND(total_revenue, 2) as total_revenue,
            total_orders,
            ROUND(avg_order_value, 2) as avg_order_value,
            ROUND(cac_roi, 2) as cac_roi,
            CASE 
                WHEN cac_roi >= 5 THEN 'EXCELLENT'
                WHEN cac_roi >= 3 THEN 'GOOD'
                WHEN cac_roi >= 1 THEN 'BREAK_EVEN'
                ELSE 'LOSS'
            END as channel_effectiveness
        ORDER BY cac_roi DESC
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            return {
                "analysis_type": "customer_acquisition_cost",
                "timestamp": datetime.now().isoformat(),
                "total_channels": len(records),
                "channels": records
            }
    
    # ==================== 综合分析 (3 个) ====================
    
    def analyze_product_profitability(self) -> dict[str, Any]:
        """
        产品盈利能力分析
        
        分析各产品/品类的盈利能力，支持产品组合优化决策
        
        Returns:
            产品盈利排名
        """
        cypher = """
        MATCH (p:Product)
        
        // 获取销售数据
        OPTIONAL MATCH (p)<-[:CONTAINS]-(sale:Sale)-[:HAS_STATUS]->(status:SaleStatus)
        WHERE status.status IN ['COMPLETED', 'DELIVERED']
        OPTIONAL MATCH (sale)-[:HAS_REVENUE]->(rev:Revenue)
        OPTIONAL MATCH (sale)-[:HAS_COST]->(cost:Cost)
        
        // 获取库存成本
        OPTIONAL MATCH (p)-[:HAS_STOCK]->(s:Stock)
        
        WITH p,
             COUNT(DISTINCT sale) as total_sales,
             COALESCE(SUM(rev.amount), 0) as total_revenue,
             COALESCE(SUM(cost.amount), 0) as total_cogs,
             COALESCE(s.quantity, 0) as current_stock,
             COALESCE(s.unit_cost, p.cost, 0) as unit_cost
        
        WHERE total_sales > 0
        
        // 计算盈利指标
        WITH p, total_sales, total_revenue, total_cogs, current_stock, unit_cost,
             (total_revenue - total_cogs) as gross_profit,
             CASE WHEN total_revenue > 0 THEN (total_revenue - total_cogs) / total_revenue * 100 ELSE 0 END as gross_margin_percent,
             total_revenue / total_sales as avg_revenue_per_sale
        
        RETURN 
            p.id as product_id,
            p.name as product_name,
            p.category as category,
            total_sales,
            ROUND(total_revenue, 2) as total_revenue,
            ROUND(total_cogs, 2) as total_cogs,
            ROUND(gross_profit, 2) as gross_profit,
            ROUND(gross_margin_percent, 2) as gross_margin_percent,
            ROUND(avg_revenue_per_sale, 2) as avg_revenue_per_sale,
            current_stock,
            CASE 
                WHEN gross_margin_percent >= 40 THEN 'HIGHLY_PROFITABLE'
                WHEN gross_margin_percent >= 25 THEN 'PROFITABLE'
                WHEN gross_margin_percent >= 10 THEN 'LOW_MARGIN'
                ELSE 'UNPROFITABLE'
            END as profitability_tier
        ORDER BY gross_profit DESC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            
            # 统计各盈利层级产品数
            tier_distribution = {}
            for r in records:
                tier = r.get('profitability_tier', 'UNKNOWN')
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            
            return {
                "analysis_type": "product_profitability",
                "timestamp": datetime.now().isoformat(),
                "total_products": len(records),
                "tier_distribution": tier_distribution,
                "products": records
            }
    
    def analyze_sales_funnel(self) -> dict[str, Any]:
        """
        销售漏斗分析
        
        分析销售转化漏斗，识别转化瓶颈
        
        Returns:
            销售漏斗转化率
        """
        cypher = """
        // 统计各阶段数量
        MATCH (lead:Lead)
        OPTIONAL MATCH (lead)-[:CONVERTED_TO]->(opp:Opportunity)
        OPTIONAL MATCH (opp)-[:HAS_STATUS]->(opp_status:OppStatus)
        OPTIONAL MATCH (opp)-[:CONVERTED_TO]->(quote:Quote)
        OPTIONAL MATCH (quote)-[:HAS_STATUS]->(quote_status:QuoteStatus)
        OPTIONAL MATCH (quote)-[:CONVERTED_TO]->(order:Order)
        OPTIONAL MATCH (order)-[:HAS_STATUS]->(order_status:OrderStatus)
        
        WITH 
             COUNT(DISTINCT lead) as leads_count,
             COUNT(DISTINCT opp) as opportunities_count,
             COUNT(DISTINCT quote) as quotes_count,
             COUNT(DISTINCT CASE WHEN order_status.status IN ['CONFIRMED', 'COMPLETED'] THEN order END) as orders_count
        
        RETURN 
            leads_count,
            opportunities_count,
            quotes_count,
            orders_count,
            CASE WHEN leads_count > 0 THEN opportunities_count * 100.0 / leads_count ELSE 0 END as lead_to_opp_rate,
            CASE WHEN opportunities_count > 0 THEN quotes_count * 100.0 / opportunities_count ELSE 0 END as opp_to_quote_rate,
            CASE WHEN quotes_count > 0 THEN orders_count * 100.0 / quotes_count ELSE 0 END as quote_to_order_rate,
            CASE WHEN leads_count > 0 THEN orders_count * 100.0 / leads_count ELSE 0 END as overall_conversion_rate
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            record = result.single()
            
            if record:
                funnel_data = dict(record)
                return {
                    "analysis_type": "sales_funnel",
                    "timestamp": datetime.now().isoformat(),
                    "funnel": funnel_data
                }
            else:
                return {
                    "analysis_type": "sales_funnel",
                    "timestamp": datetime.now().isoformat(),
                    "funnel": {}
                }
    
    def analyze_market_basket(self, min_support: int = 10) -> dict[str, Any]:
        """
        购物篮分析
        
        分析产品关联购买模式，支持交叉销售和捆绑销售决策
        
        Returns:
            产品关联规则
        """
        cypher = """
        // 查找经常一起购买的产品对
        MATCH (p1:Product)<-[:CONTAINS]-(order:Order)-[:CONTAINS]->(p2:Product)
        WHERE p1 <> p2
        
        WITH p1, p2, COUNT(DISTINCT order) as co_occurrence
        WHERE co_occurrence >= $min_support
        
        // 计算支持度和置信度
        WITH p1, p2, co_occurrence,
             SIZE((p1)<-[:CONTAINS]-()) as p1_total_orders,
             SIZE((p2)<-[:CONTAINS]-()) as p2_total_orders
        
        WITH p1, p2, co_occurrence, p1_total_orders, p2_total_orders,
             co_occurrence * 1.0 / SIZE((:Order)-[:CONTAINS]->(:Product)) as support,
             co_occurrence * 1.0 / p1_total_orders as confidence_p1_to_p2,
             co_occurrence * 1.0 / p2_total_orders as confidence_p2_to_p1,
             (co_occurrence * 1.0 / SIZE((:Order)-[:CONTAINS]->(:Product))) / 
             (p1_total_orders * 1.0 / SIZE((:Order)-[:CONTAINS]->(:Product)) * 
              p2_total_orders * 1.0 / SIZE((:Order)-[:CONTAINS]->(:Product))) as lift
        
        RETURN 
            p1.id as product1_id,
            p1.name as product1_name,
            p2.id as product2_id,
            p2.name as product2_name,
            co_occurrence,
            ROUND(support * 100, 2) as support_percent,
            ROUND(confidence_p1_to_p2 * 100, 2) as confidence_p1_to_p2_percent,
            ROUND(confidence_p2_to_p1 * 100, 2) as confidence_p2_to_p1_percent,
            ROUND(lift, 2) as lift,
            CASE 
                WHEN lift >= 3 THEN 'STRONG_ASSOCIATION'
                WHEN lift >= 2 THEN 'MODERATE_ASSOCIATION'
                ELSE 'WEAK_ASSOCIATION'
            END as association_strength,
            CASE 
                WHEN lift >= 2 THEN 'BUNDLE_RECOMMENDED'
                WHEN lift >= 1.5 THEN 'CROSS_SELL_RECOMMENDED'
                ELSE 'MONITOR'
            END as recommendation
        ORDER BY lift DESC, co_occurrence DESC
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, min_support=min_support)
            records = [dict(record) for record in result]
            
            strong_count = sum(1 for r in records if r.get('association_strength') == 'STRONG_ASSOCIATION')
            
            return {
                "analysis_type": "market_basket",
                "timestamp": datetime.now().isoformat(),
                "min_support": min_support,
                "total_pairs": len(records),
                "strong_associations": strong_count,
                "product_pairs": records
            }