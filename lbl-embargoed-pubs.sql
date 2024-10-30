select
	distinct 
	p.doi,
	p.id as [elements_id],
	pr.[Data Source Proprietary ID] as [eschol_id],
	p.[embargo-release-date],
	p.[publication-date],
	STRING_AGG(g.[funder-name], ';') as [funder_names],
	STRING_AGG(g.[funder-reference], ';') as [funder_references]
from Publication p
	join [Publication Record] pr
		on p.id = pr.[Publication ID]
		and pr.[Data Source] = 'escholarship'
	join [Publication User Relationship] pur
		on p.id = pur.[Publication ID]
	join [User] u
		on u.id = pur.[User ID]
		and u.[Primary Group Descriptor] like ('%lbl%')
	left join [Grant Publication Relationship] gpr
		on p.id = gpr.[Publication ID]
	left join [Grant] g
		on g.id = gpr.[Grant ID]
where
	p.[embargo-release-date] is not null
	and p.[embargo-release-date] > GETDATE()
group by
	p.id,
	pr.[Data Source Proprietary ID],
	p.[publication-date],
	p.[embargo-release-date],
	p.doi
order by
	p.[publication-date] desc;