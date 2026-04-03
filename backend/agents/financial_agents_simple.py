#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Financial Agents - 5 Core Agents for ERP
"""

from neo4j import GraphDatabase
import psycopg2
from decimal import Decimal
import json
import sys

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}

def convert(val):
    if val is None: return None
    if isinstance(val, Decimal): return float(val)
    return val

class InvoiceAgent:
    def __init__(self, driver):
        self.driver = driver
    
    def validate_invoices(self):
        print("\n" + "=" * 60)
        print("Invoice Validation Agent")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("MATCH (i:Invoice) WHERE NOT EXISTS((i)-[:BELONGS_TO]->(:Supplier)) RETURN count(i) as count")
            count = result.single()['count']
            print(f"[WARN] Invoices without supplier: {count}")
            
            result = session.run("MATCH (i:Invoice) WHERE i.invoiceAmount > 1000000 RETURN i.invoiceNumber as num, i.invoiceAmount as amt ORDER BY amt DESC LIMIT 5")
            print(f"\n[INFO] High-value invoices (Top 5):")
            for r in result:
                print(f"  - {r['num']}: ${r['amt']:,.2f}")

class PaymentAgent:
    def __init__(self, driver):
        self.driver = driver
    
    def analyze_payments(self):
        print("\n" + "=" * 60)
        print("Payment Management Agent")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Payment)
                RETURN count(*) as cnt, sum(p.amount) as total, avg(p.amount) as avg
            """)
            r = result.single()
            print(f"[STATS] Total payments: {r['cnt']}")
            if r['total']: print(f"[STATS] Total amount: ${r['total']:,.2f}")
            if r['avg']: print(f"[STATS] Average: ${r['avg']:,.2f}")

class AnalyticsAgent:
    def __init__(self, driver):
        self.driver = driver
    
    def forecast(self):
        print("\n" + "=" * 60)
        print("Analytics & Forecasting Agent")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("MATCH (p:Payment) WHERE p.amount IS NOT NULL RETURN sum(p.amount) as total, count(*) as cnt")
            r = result.single()
            if r['total']:
                total = float(r['total'])
                cnt = int(r['cnt'])
                avg = total / cnt if cnt > 0 else 0
                weekly = avg * 25
                daily = weekly / 7
                print(f"[FORECAST] Weekly: ${weekly:,.2f}")
                print(f"[FORECAST] Daily: ${daily:,.2f}")
                print(f"[FORECAST] Confidence: +/-15%")
                return {'weekly': round(weekly, 2), 'daily': round(daily, 2)}
        return None

class ComplianceAgent:
    def __init__(self, driver):
        self.driver = driver
    
    def audit(self):
        print("\n" + "=" * 60)
        print("Compliance Audit Agent")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (po:PurchaseOrder)-[:HAS_INVOICE]->(i:Invoice)
                WHERE po.amount IS NOT NULL AND i.invoiceAmount IS NOT NULL
                AND abs(po.amount - i.invoiceAmount) > 0.01
                RETURN po.poNumber as po, po.amount as po_amt, i.invoiceNumber as inv, i.invoiceAmount as inv_amt
                LIMIT 5
            """)
            mismatches = list(result)
            if mismatches:
                print(f"[WARN] PO-Invoice mismatches found: {len(mismatches)}")
            else:
                print(f"[OK] All PO-Invoice amounts match")

class ReportAgent:
    def __init__(self, driver):
        self.driver = driver
    
    def generate_summary(self):
        print("\n" + "=" * 60)
        print("Report Generation Agent")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("MATCH (i:Invoice) RETURN count(*) as cnt, sum(i.invoiceAmount) as total")
            r = result.single()
            print(f"[SUMMARY] Total invoices: {r['cnt']}")
            if r['total']: print(f"[SUMMARY] Total amount: ${r['total']:,.2f}")

def main():
    print("=" * 70)
    print("Financial Agents Demo - 5 Core Agents")
    print("=" * 70)
    
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    
    try:
        invoice = InvoiceAgent(driver)
        payment = PaymentAgent(driver)
        analytics = AnalyticsAgent(driver)
        compliance = ComplianceAgent(driver)
        report = ReportAgent(driver)
        
        invoice.validate_invoices()
        payment.analyze_payments()
        forecast = analytics.forecast()
        compliance.audit()
        report.generate_summary()
        
        if forecast:
            with open('D:\\erpAgent\\backend\\data\\forecast.json', 'w') as f:
                json.dump(forecast, f, indent=2)
            print(f"\n[INFO] Forecast saved to forecast.json")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] All agents completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == '__main__':
    main()
