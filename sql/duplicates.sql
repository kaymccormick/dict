select a.representation, b.name, c.desc, d.representation,count(*) from word a join wordkind b on a.kind_id = b.id join usage c on c.word_id = a.id join meaning d on d.usage_id = c.id 
group by a.representation, b.name, c.desc, d.representation
having count(*) > 1
order by a.representation, b.name, c.desc, d.representation 
