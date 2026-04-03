# -*- coding: utf-8 -*-
"""
Sync FA/CST/HR/PA modules to Neo4j
"""

import psycopg2
from decimal import Decimal
from neo4j import GraphDatabase

# PostgreSQL config
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

# Neo4j config
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}

def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def convert_value(val):
    """Convert values for Neo4j compatibility"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float, str)):
        return val
    return str(val)

def sync_fa_to_neo4j(driver, pg_cur):
    """Sync FA (Fixed Assets) module"""
    print("="*70)
    print("Syncing FA (Fixed Assets) to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Sync Asset Categories
        pg_cur.execute("SELECT category_id, category_name, asset_type, depreciation_method, life_months, enabled_flag FROM fa_categories_b")
        categories = pg_cur.fetchall()
        
        for cat in categories:
            session.run("""
                MERGE (cat:FACategory {id: $id})
                SET cat.name = $name,
                    cat.assetType = $asset_type,
                    cat.depreciationMethod = $depr_method,
                    cat.lifeMonths = $life_months,
                    cat.enabledFlag = $enabled_flag
            """, id=cat[0], name=cat[1], asset_type=cat[2], depr_method=cat[3], 
                life_months=convert_value(cat[4]), enabled_flag=cat[5])
        
        print(f"  OK Synced {len(categories)} FA Categories")
        
        # Sync Assets
        pg_cur.execute("""
            SELECT asset_id, asset_number, asset_type, asset_status, 
                   date_placed_in_service, cost, category_id, book_type_code
            FROM fa_additions_b
        """)
        assets = pg_cur.fetchall()
        
        for asset in assets:
            session.run("""
                MERGE (asset:FixedAsset {id: $id})
                SET asset.assetNumber = $asset_number,
                    asset.assetType = $asset_type,
                    asset.status = $asset_status,
                    asset.datePlacedInService = $date_placed,
                    asset.cost = $cost,
                    asset.bookTypeCode = $book_type
            """, id=asset[0], asset_number=asset[1], asset_type=asset[2], 
                asset_status=asset[3], date_placed=str(asset[4]) if asset[4] else None,
                cost=convert_value(asset[5]), book_type=asset[7])
            
            # Link to category
            session.run("""
                MATCH (asset:FixedAsset {id: $asset_id})
                MATCH (cat:FACategory {id: $cat_id})
                MERGE (asset)-[:BELONGS_TO_CATEGORY]->(cat)
            """, asset_id=asset[0], cat_id=asset[6])
        
        print(f"  OK Synced {len(assets)} Fixed Assets")
        
        # Sync Depreciation
        pg_cur.execute("""
            SELECT deprn_id, asset_id, deprn_date, deprn_amount, ytd_deprn, net_book_value
            FROM fa_deprn_detail
            LIMIT 100
        """)
        deprn = pg_cur.fetchall()
        
        for d in deprn:
            session.run("""
                MERGE (d:FADepreciation {id: $id})
                SET d.deprnDate = $deprn_date,
                    d.deprnAmount = $deprn_amount,
                    d.ytdDeprn = $ytd_deprn,
                    d.netBookValue = $net_book_value
            """, id=d[0], deprn_date=str(d[2]) if d[2] else None,
                deprn_amount=convert_value(d[3]), ytd_deprn=convert_value(d[4]),
                net_book_value=convert_value(d[5]))
            
            session.run("""
                MATCH (d:FADepreciation {id: $deprn_id})
                MATCH (asset:FixedAsset {id: $asset_id})
                MERGE (d)-[:FOR_ASSET]->(asset)
            """, deprn_id=d[0], asset_id=d[1])
        
        print(f"  OK Synced {len(deprn)} Depreciation records")
        
        # Sync Transactions
        pg_cur.execute("""
            SELECT transaction_id, asset_id, transaction_type, transaction_date, amount, status
            FROM fa_transactions
            LIMIT 100
        """)
        txns = pg_cur.fetchall()
        
        for txn in txns:
            session.run("""
                MERGE (txn:FATransaction {id: $id})
                SET txn.transactionType = $txn_type,
                    txn.transactionDate = $txn_date,
                    txn.amount = $amount,
                    txn.status = $status
            """, id=txn[0], txn_type=txn[2], txn_date=str(txn[3]) if txn[3] else None,
                amount=convert_value(txn[4]), status=txn[5])
            
            session.run("""
                MATCH (txn:FATransaction {id: $txn_id})
                MATCH (asset:FixedAsset {id: $asset_id})
                MERGE (txn)-[:FOR_ASSET]->(asset)
            """, txn_id=txn[0], asset_id=txn[1])
        
        print(f"  OK Synced {len(txns)} Transactions")
        
        return len(categories), len(assets), len(deprn), len(txns)

def sync_hr_to_neo4j(driver, pg_cur):
    """Sync HR (Human Resources) module"""
    print("\n" + "="*70)
    print("Syncing HR (Human Resources) to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Sync Jobs
        pg_cur.execute("SELECT job_id, job_name, job_code, organization_id FROM per_jobs_f")
        jobs = pg_cur.fetchall()
        
        for job in jobs:
            session.run("""
                MERGE (job:Job {id: $id})
                SET job.name = $name,
                    job.code = $code,
                    job.organizationId = $org_id
            """, id=job[0], name=job[1], code=job[2], org_id=job[3])
        
        print(f"  OK Synced {len(jobs)} Jobs")
        
        # Sync Positions
        pg_cur.execute("""
            SELECT position_id, position_name, position_code, organization_id, job_id, headcount
            FROM per_positions_f
        """)
        positions = pg_cur.fetchall()
        
        for pos in positions:
            session.run("""
                MERGE (pos:Position {id: $id})
                SET pos.name = $name,
                    pos.code = $code,
                    pos.organizationId = $org_id,
                    pos.jobId = $job_id,
                    pos.headcount = $headcount
            """, id=pos[0], name=pos[1], code=pos[2], org_id=pos[3], 
                job_id=pos[4], headcount=pos[5])
        
        print(f"  OK Synced {len(positions)} Positions")
        
        # Sync Assignments
        pg_cur.execute("""
            SELECT assignment_id, employee_id, organization_id, job_id, position_id,
                   assignment_type, assignment_status, primary_flag
            FROM per_assignments_f
            LIMIT 100
        """)
        assignments = pg_cur.fetchall()
        
        for asn in assignments:
            session.run("""
                MERGE (asn:Assignment {id: $id})
                SET asn.assignmentType = $asn_type,
                    asn.assignmentStatus = $asn_status,
                    asn.primaryFlag = $primary_flag,
                    asn.organizationId = $org_id
            """, id=asn[0], asn_type=asn[5], asn_status=asn[6], 
                primary_flag=asn[7] if len(asn) > 7 else 'N', org_id=asn[2])
            
            # Link to employee
            session.run("""
                MATCH (asn:Assignment {id: $asn_id})
                MATCH (emp:Employee {id: $emp_id})
                MERGE (asn)-[:BELONGS_TO_EMPLOYEE]->(emp)
            """, asn_id=asn[0], emp_id=asn[1])
            
            # Link to job
            session.run("""
                MATCH (asn:Assignment {id: $asn_id})
                MATCH (job:Job {id: $job_id})
                MERGE (asn)-[:HAS_JOB]->(job)
            """, asn_id=asn[0], job_id=asn[3])
            
            # Link to position
            session.run("""
                MATCH (asn:Assignment {id: $asn_id})
                MATCH (pos:Position {id: $pos_id})
                MERGE (asn)-[:HAS_POSITION]->(pos)
            """, asn_id=asn[0], pos_id=asn[4])
        
        print(f"  OK Synced {len(assignments)} Assignments")
        
        # Sync Pay Proposals
        pg_cur.execute("""
            SELECT proposal_id, assignment_id, salary_amount, currency_code, approved_flag
            FROM per_pay_proposals_f
            LIMIT 100
        """)
        proposals = pg_cur.fetchall()
        
        for prop in proposals:
            session.run("""
                MERGE (prop:PayProposal {id: $id})
                SET prop.salaryAmount = $amount,
                    prop.currencyCode = $currency,
                    prop.approvedFlag = $approved
            """, id=prop[0], amount=convert_value(prop[2]), 
                currency=prop[3], approved=prop[4] if len(prop) > 4 else 'N')
            
            session.run("""
                MATCH (prop:PayProposal {id: $prop_id})
                MATCH (asn:Assignment {id: $asn_id})
                MERGE (prop)-[:FOR_ASSIGNMENT]->(asn)
            """, prop_id=prop[0], asn_id=prop[1])
        
        print(f"  OK Synced {len(proposals)} Pay Proposals")
        
        return len(jobs), len(positions), len(assignments), len(proposals)

def sync_pa_to_neo4j(driver, pg_cur):
    """Sync PA (Projects) module"""
    print("\n" + "="*70)
    print("Syncing PA (Projects) to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Sync Projects
        pg_cur.execute("""
            SELECT project_id, project_number, project_name, project_type, 
                   status_code, budget_amount, actual_cost
            FROM pa_projects_all
        """)
        projects = pg_cur.fetchall()
        
        for proj in projects:
            session.run("""
                MERGE (proj:Project {id: $id})
                SET proj.projectNumber = $proj_num,
                    proj.name = $proj_name,
                    proj.type = $proj_type,
                    proj.statusCode = $status,
                    proj.budgetAmount = $budget,
                    proj.actualCost = $actual
            """, id=proj[0], proj_num=proj[1], proj_name=proj[2], 
                proj_type=proj[3], status=proj[4], 
                budget=convert_value(proj[5]), actual=convert_value(proj[6]))
        
        print(f"  OK Synced {len(projects)} Projects")
        
        # Sync Tasks
        pg_cur.execute("""
            SELECT task_id, project_id, task_number, task_name, parent_task_id
            FROM pa_tasks
            LIMIT 200
        """)
        tasks = pg_cur.fetchall()
        
        for task in tasks:
            session.run("""
                MERGE (task:Task {id: $id})
                SET task.taskNumber = $task_num,
                    task.name = $task_name,
                    task.parentTaskId = $parent_id
            """, id=task[0], task_num=task[2], task_name=task[3], 
                parent_id=task[4])
            
            # Link to project
            session.run("""
                MATCH (task:Task {id: $task_id})
                MATCH (proj:Project {id: $proj_id})
                MERGE (task)-[:BELONGS_TO_PROJECT]->(proj)
            """, task_id=task[0], proj_id=task[1])
        
        print(f"  OK Synced {len(tasks)} Tasks")
        
        # Sync Expenditures
        pg_cur.execute("""
            SELECT expenditure_id, project_id, task_id, expenditure_type, 
                   raw_cost, burdened_cost, status_code
            FROM pa_expenditures_all
            LIMIT 200
        """)
        expenditures = pg_cur.fetchall()
        
        for exp in expenditures:
            session.run("""
                MERGE (exp:Expenditure {id: $id})
                SET exp.expenditureType = $exp_type,
                    exp.rawCost = $raw_cost,
                    exp.burdenedCost = $burdened_cost,
                    exp.statusCode = $status
            """, id=exp[0], exp_type=exp[3], 
                raw_cost=convert_value(exp[4]), burdened_cost=convert_value(exp[5]),
                status=exp[6])
            
            # Link to project
            session.run("""
                MATCH (exp:Expenditure {id: $exp_id})
                MATCH (proj:Project {id: $proj_id})
                MERGE (exp)-[:FOR_PROJECT]->(proj)
            """, exp_id=exp[0], proj_id=exp[1])
            
            # Link to task
            session.run("""
                MATCH (exp:Expenditure {id: $exp_id})
                MATCH (task:Task {id: $task_id})
                MERGE (exp)-[:FOR_TASK]->(task)
            """, exp_id=exp[0], task_id=exp[2])
        
        print(f"  OK Synced {len(expenditures)} Expenditures")
        
        return len(projects), len(tasks), len(expenditures)

def sync_cst_to_neo4j(driver, pg_cur):
    """Sync CST (Cost Management) module"""
    print("\n" + "="*70)
    print("Syncing CST (Cost Management) to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Sync Cost Types
        pg_cur.execute("SELECT cost_type_id, cost_type, description, cost_method FROM cst_cost_types")
        cost_types = pg_cur.fetchall()
        
        for ct in cost_types:
            session.run("""
                MERGE (ct:CostType {id: $id})
                SET ct.name = $name,
                    ct.description = $desc,
                    ct.method = $method
            """, id=ct[0], name=ct[1], desc=ct[2], method=ct[3])
        
        print(f"  OK Synced {len(cost_types)} Cost Types")
        
        # Sync Cost Elements
        pg_cur.execute("SELECT cost_element_id, cost_element, element_type, description FROM cst_cost_elements")
        cost_elements = pg_cur.fetchall()
        
        for ce in cost_elements:
            session.run("""
                MERGE (ce:CostElement {id: $id})
                SET ce.name = $name,
                    ce.elementType = $elem_type,
                    ce.description = $desc
            """, id=ce[0], name=ce[1], elem_type=ce[2], desc=ce[3])
        
        print(f"  OK Synced {len(cost_elements)} Cost Elements")
        
        # Sync Item Costs
        pg_cur.execute("""
            SELECT cost_id, inventory_item_id, cost_type, material_cost, 
                   material_overhead_cost, resource_cost, overhead_cost, 
                   outside_processing_cost, total_cost
            FROM cst_item_costs
            LIMIT 100
        """)
        item_costs = pg_cur.fetchall()
        
        for ic in item_costs:
            session.run("""
                MERGE (ic:ItemCost {id: $id})
                SET ic.costType = $cost_type,
                    ic.materialCost = $material,
                    ic.materialOverheadCost = $material_oh,
                    ic.resourceCost = $resource,
                    ic.overheadCost = $overhead,
                    ic.outsideProcessingCost = $osp,
                    ic.totalCost = $total
            """, id=ic[0], cost_type=ic[2], material=convert_value(ic[3]),
                material_oh=convert_value(ic[4]), resource=convert_value(ic[5]),
                overhead=convert_value(ic[6]), osp=convert_value(ic[7]),
                total=convert_value(ic[8]))
            
            # Link to inventory item
            session.run("""
                MATCH (ic:ItemCost {id: $cost_id})
                MATCH (item:InventoryItem {id: $item_id})
                MERGE (ic)-[:FOR_ITEM]->(item)
            """, cost_id=ic[0], item_id=ic[1])
        
        print(f"  OK Synced {len(item_costs)} Item Costs")
        
        return len(cost_types), len(cost_elements), len(item_costs)

def verify_sync(driver):
    """Verify sync results"""
    print("\n" + "="*70)
    print("Verifying Sync Results...")
    print("="*70)
    
    with driver.session() as session:
        # Count new node types
        result = session.run("""
            MATCH (n)
            WHERE labels(n)[0] IN ['FixedAsset', 'FACategory', 'FADepreciation', 'FATransaction',
                                   'Job', 'Position', 'Assignment', 'PayProposal',
                                   'Project', 'Task', 'Expenditure',
                                   'CostType', 'CostElement', 'ItemCost']
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nNew Node Types:")
        print("-" * 50)
        total_nodes = 0
        for record in result:
            print(f"  {record['label']:25s}: {record['count']}")
            total_nodes += record['count']
        
        # Count new relationships
        result = session.run("""
            MATCH ()-[r]->()
            WHERE type(r) IN ['BELONGS_TO_CATEGORY', 'FOR_ASSET', 'HAS_JOB', 
                              'HAS_POSITION', 'BELONGS_TO_EMPLOYEE', 'FOR_ASSIGNMENT',
                              'BELONGS_TO_PROJECT', 'FOR_PROJECT', 'FOR_TASK', 'FOR_ITEM']
            RETURN type(r) as type, count(r) as count
            ORDER BY type
        """)
        
        print("\nNew Relationships:")
        print("-" * 50)
        total_rels = 0
        for record in result:
            print(f"  {record['type']:25s}: {record['count']}")
            total_rels += record['count']
        
        print("\n" + "="*50)
        print(f"  Total New Nodes: {total_nodes}")
        print(f"  Total New Relationships: {total_rels}")
        print("="*50)

def main():
    print("="*70)
    print("Sync FA/CST/HR/PA Modules to Neo4j")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        # Sync FA
        fa_stats = sync_fa_to_neo4j(driver, pg_cur)
        
        # Sync HR
        hr_stats = sync_hr_to_neo4j(driver, pg_cur)
        
        # Sync PA
        pa_stats = sync_pa_to_neo4j(driver, pg_cur)
        
        # Sync CST
        cst_stats = sync_cst_to_neo4j(driver, pg_cur)
        
        # Verify
        verify_sync(driver)
        
        print("\n" + "="*70)
        print("OK Sync completed successfully!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  FA: {fa_stats[0]} categories, {fa_stats[1]} assets, {fa_stats[2]} deprn, {fa_stats[3]} txns")
        print(f"  HR: {hr_stats[0]} jobs, {hr_stats[1]} positions, {hr_stats[2]} assignments, {hr_stats[3]} proposals")
        print(f"  PA: {pa_stats[0]} projects, {pa_stats[1]} tasks, {pa_stats[2]} expenditures")
        print(f"  CST: {cst_stats[0]} cost types, {cst_stats[1]} cost elements, {cst_stats[2]} item costs")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR Error during sync: {e}")
        raise
    finally:
        pg_cur.close()
        pg_conn.close()
        driver.close()

if __name__ == '__main__':
    main()
