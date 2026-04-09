# -*- coding: utf-8 -*-
"""
Sync HR (Human Resources) data to Neo4j
Creates test data for employee management module
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
        # Clear existing HR data
        print('[INFO] Clearing existing HR data...')
        session.run('MATCH (n:Employee) DETACH DELETE n')
        session.run('MATCH (n:Department) DETACH DELETE n')
        session.run('MATCH (n:Position) DETACH DELETE n')
        
        # 1. Create Departments
        print('[INFO] Creating Departments...')
        departments = [
            {'id': 'DEPT_001', 'name': '总经办', 'code': 'GM'},
            {'id': 'DEPT_002', 'name': '财务部', 'code': 'FIN'},
            {'id': 'DEPT_003', 'name': '人力资源部', 'code': 'HR'},
            {'id': 'DEPT_004', 'name': '销售部', 'code': 'SALES'},
            {'id': 'DEPT_005', 'name': '采购部', 'code': 'PURCHASE'},
            {'id': 'DEPT_006', 'name': '仓储部', 'code': 'WAREHOUSE'},
        ]
        for dept in departments:
            session.run('''
                CREATE (d:Department {
                    department_id: $id,
                    name: $name,
                    code: $code,
                    created_at: datetime()
                })
            ''', **dept)
        print(f'  Created {len(departments)} departments')
        
        # 2. Create Positions
        print('[INFO] Creating Positions...')
        positions = [
            {'id': 'POS_001', 'name': '总经理', 'level': 1},
            {'id': 'POS_002', 'name': '财务总监', 'level': 2},
            {'id': 'POS_003', 'name': '会计', 'level': 3},
            {'id': 'POS_004', 'name': '出纳', 'level': 3},
            {'id': 'POS_005', 'name': '销售总监', 'level': 2},
            {'id': 'POS_006', 'name': '销售经理', 'level': 3},
            {'id': 'POS_007', 'name': '销售代表', 'level': 4},
            {'id': 'POS_008', 'name': '采购经理', 'level': 3},
            {'id': 'POS_009', 'name': '采购员', 'level': 4},
            {'id': 'POS_010', 'name': '仓库主管', 'level': 3},
            {'id': 'POS_011', 'name': '仓管员', 'level': 4},
            {'id': 'POS_012', 'name': 'HR 总监', 'level': 2},
            {'id': 'POS_013', 'name': 'HR 专员', 'level': 3},
        ]
        for pos in positions:
            session.run('''
                CREATE (p:Position {
                    position_id: $id,
                    name: $name,
                    level: $level
                })
            ''', **pos)
        print(f'  Created {len(positions)} positions')
        
        # 3. Create Employees
        print('[INFO] Creating Employees...')
        first_names = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴']
        last_names = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋']
        
        employees = []
        for i in range(1, 51):
            emp = {
                'id': f'EMP_{i:04d}',
                'name': f'{random.choice(first_names)}{random.choice(last_names)}',
                'email': f'employee{i}@company.com',
                'phone': f'138{i:04d}{random.randint(1000, 9999)}',
                'hire_date': (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500))).strftime('%Y-%m-%d'),
                'status': random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'RESIGNED', 'ON_LEAVE']),
                'salary': random.randint(5000, 50000),
            }
            employees.append(emp)
            
            dept_idx = (i - 1) % len(departments)
            pos_idx = (i - 1) % len(positions)
            
            session.run('''
                CREATE (e:Employee {
                    employee_id: $id,
                    name: $name,
                    email: $email,
                    phone: $phone,
                    hire_date: $hire_date,
                    status: $status,
                    salary: $salary
                })
                WITH e
                MATCH (d:Department) WHERE d.department_id = $dept_id
                CREATE (e)-[:BELONGS_TO]->(d)
                WITH e
                MATCH (p:Position) WHERE p.position_id = $pos_id
                CREATE (e)-[:HAS_POSITION]->(p)
            ''', dept_id=departments[dept_idx]['id'], pos_id=positions[pos_idx]['id'], **emp)
        print(f'  Created {len(employees)} employees')
        
        # 4. Create Manager Relationships
        print('[INFO] Creating Manager Relationships...')
        manager_count = 0
        for i, emp in enumerate(employees):
            if i < 10:  # First 10 employees are managers
                # Find subordinates
                subordinates = employees[i+10:i+20] if i+10 < len(employees) else []
                for sub in subordinates:
                    session.run('''
                        MATCH (mgr:Employee {employee_id: $mgr_id})
                        MATCH (sub:Employee {employee_id: $sub_id})
                        MERGE (mgr)-[:MANAGES]->(sub)
                    ''', mgr_id=emp['id'], sub_id=sub['id'])
                    manager_count += 1
        print(f'  Created {manager_count} manager relationships')
        
        # 5. Link to existing data
        print('[INFO] Linking HR to existing data...')
        session.run('''
            MATCH (e:Employee), (s:Sale)
            WHERE e.status = 'ACTIVE'
            WITH e, s LIMIT 50
            MERGE (e)-[:RESPONSIBLE_FOR]->(s)
        ''')
        session.run('''
            MATCH (e:Employee), (po:PurchaseOrder)
            WHERE e.status = 'ACTIVE'
            WITH e, po LIMIT 50
            MERGE (e)-[:RESPONSIBLE_FOR]->(po)
        ''')
        print('  Created links to Sales and PurchaseOrders')
        
        # Verify counts
        print('\n[INFO] Verifying data...')
        result = session.run('MATCH (n:Department) RETURN count(n) as count')
        print(f'  Department: {result.single()["count"]}')
        result = session.run('MATCH (n:Position) RETURN count(n) as count')
        print(f'  Position: {result.single()["count"]}')
        result = session.run('MATCH (n:Employee) RETURN count(n) as count')
        print(f'  Employee: {result.single()["count"]}')
        result = session.run('MATCH ()-[r:MANAGES]->() RETURN count(r) as count')
        print(f'  MANAGES relationships: {result.single()["count"]}')
        
        # Total nodes
        result = session.run('MATCH (n) RETURN count(n) as count')
        total = result.single()['count']
        print(f'\n[OK] Total nodes in Neo4j: {total}')
    
    driver.close()
    print('\n[OK] HR data sync completed!')

if __name__ == '__main__':
    main()