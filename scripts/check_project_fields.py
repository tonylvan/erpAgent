from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("检查 Project 字段:")
r = s.run("MATCH (p:Project) RETURN p{.*} LIMIT 1")
for rec in r:
    print(rec['p'])

d.close()
