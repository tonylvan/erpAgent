# -*- coding: utf-8 -*-
"""
Sync GL (General Ledger) and XLA (Subledger Accounting) data to Neo4j
Creates test data for GSD knowledge graph
"""

from neo4j import GraphDatabase
import random
from datetime import datetime, timedelta

# Neo4j connection
NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

def main():
    print('[INFO] Connecting to Neo4j...')
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Clear existing GL/XLA data
        print('[INFO] Clearing existing GL/XLA data...')
        session.run('MATCH (n:GLLedger) DETACH DELETE n')
        session.run('MATCH (n:GLPeriod) DETACH DELETE n')
        session.run('MATCH (n:GLAccount) DETACH DELETE n')
        session.run('MATCH (n:GLBatch) DETACH DELETE n')
        session.run('MATCH (n:GLJournal) DETACH DELETE n')
        session.run('MATCH (n:XLAEvent) DETACH DELETE n')
        session.run('MATCH (n:AccountingEntry) DETACH DELETE n')
        
        # 1. Create GL Ledgers
        print('[INFO] Creating GL Ledgers...')
        ledgers = [
            {'id': 'LEDGER_001', 'name': '主账套', 'currency': 'CNY', 'type': 'PRIMARY'},
            {'id': 'LEDGER_002', 'name': '子账套', 'currency': 'USD', 'type': 'SECONDARY'}
        ]
        for ledger in ledgers:
            session.run('''
                CREATE (l:GLLedger {
                    ledger_id: $id,
                    name: $name,
                    currency: $currency,
                    type: $type,
                    created_at: datetime()
                })
            ''', **ledger)
        print(f'  Created {len(ledgers)} ledgers')
        
        # 2. Create GL Periods (2026)
        print('[INFO] Creating GL Periods...')
        periods = []
        for month in range(1, 13):
            period = {
                'id': f'PERIOD_2026_{month:02d}',
                'name': f'2026年{month}月',
                'year': 2026,
                'month': month,
                'quarter': (month - 1) // 3 + 1,
                'status': 'OPEN' if month >= 4 else 'CLOSED'
            }
            periods.append(period)
            session.run('''
                CREATE (p:GLPeriod {
                    period_id: $id,
                    name: $name,
                    year: $year,
                    month: $month,
                    quarter: $quarter,
                    status: $status
                })
                WITH p
                MATCH (l:GLLedger {ledger_id: 'LEDGER_001'})
                CREATE (p)-[:IN_LEDGER]->(l)
            ''', **period)
        print(f'  Created {len(periods)} periods')
        
        # 3. Create GL Accounts
        print('[INFO] Creating GL Accounts...')
        accounts = [
            {'id': 'ACC_1001', 'code': '1001', 'name': '库存现金', 'type': 'ASSET'},
            {'id': 'ACC_1002', 'code': '1002', 'name': '银行存款', 'type': 'ASSET'},
            {'id': 'ACC_1122', 'code': '1122', 'name': '应收账款', 'type': 'ASSET'},
            {'id': 'ACC_2202', 'code': '2202', 'name': '应付账款', 'type': 'LIABILITY'},
            {'id': 'ACC_2203', 'code': '2203', 'name': '预收账款', 'type': 'LIABILITY'},
            {'id': 'ACC_4001', 'code': '4001', 'name': '主营业务收入', 'type': 'REVENUE'},
            {'id': 'ACC_4002', 'code': '4002', 'name': '其他业务收入', 'type': 'REVENUE'},
            {'id': 'ACC_5001', 'code': '5001', 'name': '主营业务成本', 'type': 'EXPENSE'},
            {'id': 'ACC_5002', 'code': '5002', 'name': '其他业务成本', 'type': 'EXPENSE'},
            {'id': 'ACC_5601', 'code': '5601', 'name': '销售费用', 'type': 'EXPENSE'},
            {'id': 'ACC_5602', 'code': '5602', 'name': '管理费用', 'type': 'EXPENSE'},
            {'id': 'ACC_5603', 'code': '5603', 'name': '财务费用', 'type': 'EXPENSE'},
        ]
        for acc in accounts:
            session.run('''
                CREATE (a:GLAccount {
                    account_id: $id,
                    code: $code,
                    name: $name,
                    type: $type
                })
            ''', **acc)
        print(f'  Created {len(accounts)} accounts')
        
        # 4. Create GL Batches
        print('[INFO] Creating GL Batches...')
        batches = []
        for i in range(1, 11):
            batch = {
                'id': f'BATCH_{i:04d}',
                'name': f'日记账批次_{i}',
                'status': random.choice(['POSTED', 'UNPOSTED']),
                'total_amount': random.randint(100000, 1000000)
            }
            batches.append(batch)
            period_idx = random.randint(0, 11)
            session.run('''
                CREATE (b:GLBatch {
                    batch_id: $id,
                    name: $name,
                    status: $status,
                    total_amount: $total_amount,
                    created_at: datetime()
                })
                WITH b
                MATCH (p:GLPeriod)
                WHERE p.period_id = $period_id
                CREATE (b)-[:IN_PERIOD]->(p)
            ''', period_id=periods[period_idx]['id'], **batch)
        print(f'  Created {len(batches)} batches')
        
        # 5. Create GL Journals
        print('[INFO] Creating GL Journals...')
        journals = []
        for i in range(1, 31):
            journal = {
                'id': f'JE_{i:05d}',
                'name': f'日记账_{i}',
                'description': f'业务凭证_{i}',
                'amount': random.randint(10000, 100000),
                'status': 'POSTED'
            }
            journals.append(journal)
            batch_idx = (i - 1) // 3
            acc_idx = random.randint(0, len(accounts) - 1)
            session.run('''
                CREATE (j:GLJournal {
                    journal_id: $id,
                    name: $name,
                    description: $description,
                    amount: $amount,
                    status: $status,
                    created_at: datetime()
                })
                WITH j
                MATCH (b:GLBatch {batch_id: $batch_id})
                CREATE (j)-[:BELONGS_TO]->(b)
                WITH j
                MATCH (a:GLAccount {account_id: $acc_id})
                CREATE (j)-[:DEBITS]->(a)
            ''', batch_id=batches[batch_idx]['id'], acc_id=accounts[acc_idx]['id'], **journal)
        print(f'  Created {len(journals)} journals')
        
        # 6. Create XLA Events
        print('[INFO] Creating XLA Events...')
        event_types = ['INVOICE_CREATED', 'PAYMENT_RECEIVED', 'PO_APPROVED', 'INVOICE_PAID']
        xla_events = []
        for i in range(1, 51):
            event = {
                'id': f'XLA_EVT_{i:05d}',
                'event_type': random.choice(event_types),
                'event_date': (datetime(2026, 4, 1) + timedelta(days=random.randint(0, 7))).isoformat(),
                'amount': random.randint(10000, 500000),
                'status': 'PROCESSED'
            }
            xla_events.append(event)
            session.run('''
                CREATE (e:XLAEvent {
                    event_id: $id,
                    event_type: $event_type,
                    event_date: $event_date,
                    amount: $amount,
                    status: $status
                })
            ''', **event)
        print(f'  Created {len(xla_events)} XLA events')
        
        # 7. Create Accounting Entries
        print('[INFO] Creating Accounting Entries...')
        for i in range(1, 51):
            entry = {
                'id': f'AE_{i:05d}',
                'description': f'会计分录_{i}',
                'debit_amount': random.randint(10000, 100000),
                'credit_amount': random.randint(10000, 100000)
            }
            event_idx = (i - 1) % len(xla_events)
            acc_idx = random.randint(0, len(accounts) - 1)
            session.run('''
                CREATE (ae:AccountingEntry {
                    entry_id: $id,
                    description: $description,
                    debit_amount: $debit_amount,
                    credit_amount: $credit_amount
                })
                WITH ae
                MATCH (e:XLAEvent {event_id: $event_id})
                CREATE (ae)-[:FOR_EVENT]->(e)
                WITH ae
                MATCH (a:GLAccount {account_id: $acc_id})
                CREATE (ae)-[:USES_ACCOUNT]->(a)
            ''', event_id=xla_events[event_idx]['id'], acc_id=accounts[acc_idx]['id'], **entry)
        print(f'  Created 50 accounting entries')
        
        # 8. Link Invoices and Payments to XLA Events
        print('[INFO] Linking Invoices/Payments to XLA Events...')
        session.run('''
            MATCH (i:Invoice), (e:XLAEvent)
            WHERE e.event_type = 'INVOICE_CREATED'
            WITH i, e LIMIT 50
            CREATE (i)-[:GENERATED]->(e)
        ''')
        session.run('''
            MATCH (p:Payment), (e:XLAEvent)
            WHERE e.event_type = 'PAYMENT_RECEIVED' OR e.event_type = 'INVOICE_PAID'
            WITH p, e LIMIT 50
            CREATE (p)-[:GENERATED]->(e)
        ''')
        print('  Created relationships')
        
        # Verify counts
        print('\n[INFO] Verifying data...')
        result = session.run('MATCH (n:GLLedger) RETURN count(n) as count')
        print(f'  GLLedger: {result.single()["count"]}')
        result = session.run('MATCH (n:GLPeriod) RETURN count(n) as count')
        print(f'  GLPeriod: {result.single()["count"]}')
        result = session.run('MATCH (n:GLAccount) RETURN count(n) as count')
        print(f'  GLAccount: {result.single()["count"]}')
        result = session.run('MATCH (n:GLBatch) RETURN count(n) as count')
        print(f'  GLBatch: {result.single()["count"]}')
        result = session.run('MATCH (n:GLJournal) RETURN count(n) as count')
        print(f'  GLJournal: {result.single()["count"]}')
        result = session.run('MATCH (n:XLAEvent) RETURN count(n) as count')
        print(f'  XLAEvent: {result.single()["count"]}')
        result = session.run('MATCH (n:AccountingEntry) RETURN count(n) as count')
        print(f'  AccountingEntry: {result.single()["count"]}')
        
        # Total nodes
        result = session.run('MATCH (n) RETURN count(n) as count')
        total = result.single()['count']
        print(f'\n[OK] Total nodes in Neo4j: {total}')
    
    driver.close()
    print('\n[OK] GL/XLA data sync completed!')

if __name__ == '__main__':
    main()