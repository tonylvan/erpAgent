from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()
r = s.run('MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC')
for rec in r:
    label = rec['label'] if rec['label'] else 'Unknown'
    print(f'{label:30s}: {rec["count"]}')
d.close()
