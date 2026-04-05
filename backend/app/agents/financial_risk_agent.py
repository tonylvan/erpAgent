# -*- coding: utf-8 -*-
"""财务风险检测 Agent - 5 类 20 条规则"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

class RiskSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    WARNING = "WARNING"

class RiskType(str, Enum):
    CASHFLOW_CRITICAL = "cashflow_critical"
    CASHFLOW_BURN_RATE = "cashflow_burn_rate"
    CASHFLOW_RUNWAY = "cashflow_runway"
    CASHFLOW_NEGATIVE = "cashflow_negative"
    AR_OVERDUE_RATE = "ar_overdue_rate"
    AR_CONCENTRATION = "ar_concentration"
    AR_DSO = "ar_dso"
    AR_BAD_DEBT = "ar_bad_debt"
    AP_PAYMENT_PRESSURE = "ap_payment_pressure"
    AP_SUPPLIER_CONCENTRATION = "ap_supplier_concentration"
    AP_OVERDUE_PAYMENT = "ap_overdue_payment"
    AP_DPO_ABNORMAL = "ap_dpo_abnormal"
    RATIO_CURRENT = "ratio_current"
    RATIO_DEBT_EQUITY = "ratio_debt_equity"
    RATIO_ROE = "ratio_roe"
    RATIO_ROI = "ratio_roi"
    BUDGET_DEPARTMENT = "budget_department"
    BUDGET_PROJECT = "budget_project"
    BUDGET_GROWTH = "budget_growth"
    BUDGET_REVENUE = "budget_revenue"

class FinancialRiskReport:
    def __init__(self, risk_type: str, severity: str, description: str,
                 data: Dict[str, Any], recommendation: str, impact: str):
        self.agent = "financial_risk"
        self.risk_type = risk_type
        self.severity = severity
        self.description = description
        self.data = data
        self.recommendation = recommendation
        self.impact = impact
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {"agent": self.agent, "risk_type": self.risk_type, "severity": self.severity,
                "description": self.description, "data": self.data, "recommendation": self.recommendation,
                "impact": self.impact, "created_at": self.created_at}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class DatabaseConnection:
    def __init__(self):
        self.pg_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/erpagent")
        self.pg_engine = None
        self.pg_session = None
    
    def connect_postgresql(self):
        try:
            self.pg_engine = create_engine(self.pg_url)
            self.pg_session = sessionmaker(bind=self.pg_engine)
            print("[OK] PostgreSQL 连接成功")
            return True
        except Exception as e:
            print(f"[ERROR] PostgreSQL 连接失败：{e}")
            return False
    
    def close(self):
        if self.pg_engine: self.pg_engine.dispose()
    
    def execute_pg_query(self, query: str, params: Dict = None) -> List[Dict]:
        if not self.pg_session and not self.connect_postgresql(): return []
        try:
            with self.pg_session() as session:
                return [dict(row._mapping) for row in session.execute(text(query), params or {})]
        except Exception as e:
            print(f"PostgreSQL 查询错误：{e}")
            return []

class FinancialRiskAgent:
    def __init__(self, db_connection: DatabaseConnection = None):
        self.db = db_connection or DatabaseConnection()
        self.risks: List[FinancialRiskReport] = []
    
    def connect(self): return self.db.connect_postgresql()
    def close(self): self.db.close()
    
    def detect_all_risks(self, company_id: str = None) -> List[Dict[str, Any]]:
        self.risks = []
        print(f"\n{'='*60}\n财务风险检测开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}")
        print("\n[1/5] 检测现金流风险..."); self._detect_cashflow_risks(company_id)
        print("\n[2/5] 检测应收账款风险..."); self._detect_ar_risks(company_id)
        print("\n[3/5] 检测应付账款风险..."); self._detect_ap_risks(company_id)
        print("\n[4/5] 检测财务比率异常..."); self._detect_ratio_risks(company_id)
        print("\n[5/5] 检测预算偏差风险..."); self._detect_budget_risks(company_id)
        print(f"\n{'='*60}\n检测完成！共发现 {len(self.risks)} 条风险\n{'='*60}\n")
        return [r.to_dict() for r in self.risks]
    
    def _detect_cashflow_risks(self, company_id: str = None):
        for row in self.db.execute_pg_query(
            "SELECT company_id, company_name, total_cash, monthly_operating_expenses, monthly_budget, operating_cashflow_m1, operating_cashflow_m2, operating_cashflow_m3 FROM cashflow_summary WHERE (:company_id IS NULL OR company_id = :company_id)",
            {"company_id": company_id}):
            tc = float(row.get("total_cash", 0) or 0); me = float(row.get("monthly_operating_expenses", 0) or 0)
            mb = float(row.get("monthly_budget", 0) or 0)
            o1, o2, o3 = float(row.get("operating_cashflow_m1", 0) or 0), float(row.get("operating_cashflow_m2", 0) or 0), float(row.get("operating_cashflow_m3", 0) or 0)
            if me > 0:
                m = tc / me
                if m < 3:
                    s = RiskSeverity.CRITICAL.value if m < 1 else RiskSeverity.HIGH.value if m < 2 else RiskSeverity.MEDIUM.value
                    self.risks.append(FinancialRiskReport(RiskType.CASHFLOW_CRITICAL.value, s, f"现金余额仅够{m:.1f}个月",
                        {"current_cash": tc, "monthly_burn": me, "runway_months": round(m, 2)}, "加速收款", f"现金流仅够{m:.1f}个月"))
            if mb > 0 and me > mb * 1.2:
                r = me / mb
                self.risks.append(FinancialRiskReport(RiskType.CASHFLOW_BURN_RATE.value, RiskSeverity.HIGH.value,
                    f"消耗率超标{r*100-100:.1f}%", {"ratio": round(r, 3)}, "审查费用", "成本控制问题"))
            if me > 0:
                rw = tc / me
                if rw < 6:
                    s = RiskSeverity.CRITICAL.value if rw < 3 else RiskSeverity.HIGH.value
                    self.risks.append(FinancialRiskReport(RiskType.CASHFLOW_RUNWAY.value, s, f"Runway 仅{rw:.1f}个月",
                        {"runway_months": round(rw, 2)}, "立即融资", "资金链风险"))
            if o1 < 0 and o2 < 0 and o3 < 0:
                self.risks.append(FinancialRiskReport(RiskType.CASHFLOW_NEGATIVE.value, RiskSeverity.HIGH.value,
                    "连续 3 个月经营现金流为负", {"ocf_avg": round((o1+o2+o3)/3, 2)}, "评估商业模式", "可持续性风险"))
    
    def _detect_ar_risks(self, company_id: str = None):
        p = {"company_id": company_id}
        for row in self.db.execute_pg_query("SELECT company_id, company_name, total_ar, overdue_ar, dso FROM ar_summary WHERE (:company_id IS NULL OR company_id = :company_id)", p):
            ta, oa, d = float(row.get("total_ar", 0) or 0), float(row.get("overdue_ar", 0) or 0), float(row.get("dso", 0) or 0)
            if ta > 0 and oa / ta > 0.2:
                r = oa / ta
                self.risks.append(FinancialRiskReport(RiskType.AR_OVERDUE_RATE.value, RiskSeverity.HIGH.value,
                    f"逾期率{r*100:.1f}%", {"overdue_rate": round(r, 3)}, "加强催收", "回款能力问题"))
            if d > 60:
                s = RiskSeverity.HIGH.value if d > 90 else RiskSeverity.MEDIUM.value
                self.risks.append(FinancialRiskReport(RiskType.AR_DSO.value, s, f"DSO 为{d:.1f}天",
                    {"dso_days": round(d, 1)}, "优化信用政策", "资金占用"))
        for row in self.db.execute_pg_query("SELECT customer_id, customer_name, overdue_amount, max_overdue_days, ar_90plus_amount FROM customer_ar_detail WHERE (:company_id IS NULL OR company_id = :company_id)", p):
            cn, ov, dy, a90 = row.get("customer_name", "未知"), float(row.get("overdue_amount", 0) or 0), int(row.get("max_overdue_days", 0) or 0), float(row.get("ar_90plus_amount", 0) or 0)
            if ov > 1000000:
                self.risks.append(FinancialRiskReport(RiskType.AR_CONCENTRATION.value, RiskSeverity.HIGH.value,
                    f"客户{cn}逾期{ov/10000:.1f}万元", {"overdue_amount": ov}, "重点催收", "集中度风险"))
            if dy > 90 and a90 > 500000:
                self.risks.append(FinancialRiskReport(RiskType.AR_BAD_DEBT.value, RiskSeverity.CRITICAL.value,
                    f"客户{cn}坏账风险", {"overdue_days": dy, "amount": a90}, "计提坏账", "坏账风险"))
    
    def _detect_ap_risks(self, company_id: str = None):
        p = {"company_id": company_id}
        for row in self.db.execute_pg_query("SELECT company_id, ap_due_in_7days, cash_reserve, dpo FROM ap_summary WHERE (:company_id IS NULL OR company_id = :company_id)", p):
            a7, cr, dp = float(row.get("ap_due_in_7days", 0) or 0), float(row.get("cash_reserve", 0) or 0), float(row.get("dpo", 0) or 0)
            if cr > 0 and a7 > cr * 0.5:
                self.risks.append(FinancialRiskReport(RiskType.AP_PAYMENT_PRESSURE.value, RiskSeverity.HIGH.value,
                    f"7 天内到期占现金{a7/cr*100:.1f}%", {"pressure_ratio": round(a7/cr, 3)}, "紧急融资", "付款压力"))
            if dp > 67.5:
                self.risks.append(FinancialRiskReport(RiskType.AP_DPO_ABNORMAL.value, RiskSeverity.MEDIUM.value,
                    f"DPO 为{dp:.1f}天", {"dpo": round(dp, 1)}, "检查付款", "DPO 异常"))
        sups = self.db.execute_pg_query("SELECT supplier_id, supplier_name, total_purchase, purchase_rank, overdue_payment_amount, overdue_days FROM supplier_ap_detail WHERE (:company_id IS NULL OR company_id = :company_id)", p)
        tot = sum(float(r.get("total_purchase", 0) or 0) for r in sups)
        t5 = sum(float(r.get("total_purchase", 0) or 0) for r in sorted(sups, key=lambda x: x.get("purchase_rank", 99))[:5])
        if tot > 0 and t5 / tot > 0.7:
            self.risks.append(FinancialRiskReport(RiskType.AP_SUPPLIER_CONCENTRATION.value, RiskSeverity.MEDIUM.value,
                f"前 5 大供应商占比{t5/tot*100:.1f}%", {"concentration": round(t5/tot, 3)}, "开发备选", "供应链风险"))
        for r in sups:
            sn, oa, od = r.get("supplier_name", "未知"), float(r.get("overdue_payment_amount", 0) or 0), int(r.get("overdue_days", 0) or 0)
            if od > 0 and oa > 0:
                s = RiskSeverity.HIGH.value if od > 30 else RiskSeverity.MEDIUM.value
                self.risks.append(FinancialRiskReport(RiskType.AP_OVERDUE_PAYMENT.value, s, f"供应商{sn}逾期{od}天",
                    {"overdue_days": od, "amount": oa}, "立即付款", "影响关系"))
    
    def _detect_ratio_risks(self, company_id: str = None):
        for row in self.db.execute_pg_query("SELECT company_id, current_ratio, quick_ratio, debt_to_equity, roe, roi, total_liabilities, equity FROM financial_ratios WHERE (:company_id IS NULL OR company_id = :company_id)", {"company_id": company_id}):
            cr, dte, roe, roi = float(row.get("current_ratio", 0) or 0), float(row.get("debt_to_equity", 0) or 0), float(row.get("roe", 0) or 0), float(row.get("roi", 0) or 0)
            if 0 < cr < 1.5:
                s = RiskSeverity.CRITICAL.value if cr < 1.0 else RiskSeverity.WARNING.value
                self.risks.append(FinancialRiskReport(RiskType.RATIO_CURRENT.value, s, f"流动比率{cr:.2f}",
                    {"current_ratio": round(cr, 2)}, "优化资产", "偿债能力不足"))
            if dte > 2.0:
                s = RiskSeverity.CRITICAL.value if dte > 3.0 else RiskSeverity.HIGH.value
                self.risks.append(FinancialRiskReport(RiskType.RATIO_DEBT_EQUITY.value, s, f"负债权益比{dte:.2f}",
                    {"debt_to_equity": round(dte, 2)}, "降低负债", "杠杆风险"))
            if roe < 0.05:
                s = RiskSeverity.HIGH.value if roe < 0 else RiskSeverity.WARNING.value
                self.risks.append(FinancialRiskReport(RiskType.RATIO_ROE.value, s, f"ROE 为{roe*100:.2f}%",
                    {"roe": round(roe, 4)}, "提升效率", "回报不足"))
            if roi < 0.08:
                self.risks.append(FinancialRiskReport(RiskType.RATIO_ROI.value, RiskSeverity.MEDIUM.value,
                    f"ROI 为{roi*100:.2f}%", {"roi": round(roi, 4)}, "优化投资", "投资效率低"))
    
    def _detect_budget_risks(self, company_id: str = None):
        p = {"company_id": company_id}
        for row in self.db.execute_pg_query("SELECT department_name, budget_amount, actual_amount, prev_month_actual FROM department_budget_variance WHERE (:company_id IS NULL OR company_id = :company_id)", p):
            dn, b, a, pv = row.get("department_name", "未知"), float(row.get("budget_amount", 0) or 0), float(row.get("actual_amount", 0) or 0), float(row.get("prev_month_actual", 0) or 0)
            if b > 0 and a > b * 1.2:
                r = a / b
                s = RiskSeverity.HIGH.value if r > 1.5 else RiskSeverity.MEDIUM.value
                self.risks.append(FinancialRiskReport(RiskType.BUDGET_DEPARTMENT.value, s, f"部门{dn}超预算{r*100-100:.1f}%",
                    {"variance_ratio": round(r, 3)}, "审查超支", "成本控制失效"))
            if pv > 0 and a > pv * 1.5:
                g = (a - pv) / pv
                self.risks.append(FinancialRiskReport(RiskType.BUDGET_GROWTH.value, RiskSeverity.MEDIUM.value,
                    f"部门{dn}费用增长{g*100:.1f}%", {"growth_rate": round(g, 3)}, "分析原因", "费用异常"))
        for row in self.db.execute_pg_query("SELECT project_name, budget_cost, actual_cost FROM project_budget_variance WHERE (:company_id IS NULL OR company_id = :company_id)", p):
            pn, b, a = row.get("project_name", "未知"), float(row.get("budget_cost", 0) or 0), float(row.get("actual_cost", 0) or 0)
            if b > 0 and a > b * 1.3:
                r = a / b
                self.risks.append(FinancialRiskReport(RiskType.BUDGET_PROJECT.value, RiskSeverity.HIGH.value,
                    f"项目{pn}超支{r*100-100:.1f}%", {"overrun_ratio": round(r, 3)}, "控制成本", "管理问题"))
        for row in self.db.execute_pg_query("SELECT budget_revenue, actual_revenue FROM revenue_budget_variance WHERE (:company_id IS NULL OR company_id = :company_id)", p):
            b, a = float(row.get("budget_revenue", 0) or 0), float(row.get("actual_revenue", 0) or 0)
            if b > 0 and a < b * 0.8:
                r = a / b
                self.risks.append(FinancialRiskReport(RiskType.BUDGET_REVENUE.value, RiskSeverity.HIGH.value,
                    f"收入达成率{r*100:.1f}%", {"achievement_rate": round(r, 3)}, "调整策略", "业务问题"))
    
    def get_risk_summary(self) -> Dict[str, Any]:
        if not self.risks: return {"total": 0, "by_severity": {}, "critical_count": 0, "high_count": 0, "medium_count": 0, "warning_count": 0}
        by_sev = {}
        for r in self.risks: by_sev[r.severity] = by_sev.get(r.severity, 0) + 1
        return {"total": len(self.risks), "by_severity": by_sev,
                "critical_count": by_sev.get(RiskSeverity.CRITICAL.value, 0),
                "high_count": by_sev.get(RiskSeverity.HIGH.value, 0),
                "medium_count": by_sev.get(RiskSeverity.MEDIUM.value, 0),
                "warning_count": by_sev.get(RiskSeverity.WARNING.value, 0)}
    
    def export_risks(self, filepath: str = None) -> str:
        if not filepath: filepath = f"financial_risks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, "w", encoding="utf-8") as f: json.dump([r.to_dict() for r in self.risks], f, ensure_ascii=False, indent=2)
        return filepath

def run_financial_risk_detection(company_id: str = None) -> List[Dict[str, Any]]:
    agent = FinancialRiskAgent()
    if not agent.connect(): print("[ERROR] 数据库连接失败"); return []
    try: return agent.detect_all_risks(company_id)
    finally: agent.close()

def get_financial_risk_agent() -> FinancialRiskAgent:
    return FinancialRiskAgent()

if __name__ == "__main__":
    risks = run_financial_risk_detection()
    print(f"\n检测到 {len(risks)} 条风险\n")
    for r in risks: print(f"[{r['severity']}] {r['risk_type']}: {r['description']}")
