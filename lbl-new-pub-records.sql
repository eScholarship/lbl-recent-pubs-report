SET TRANSACTION ISOLATION LEVEL SNAPSHOT
BEGIN TRANSACTION;

DECLARE @ninety_days_ago AS DATE = DATEADD(day,-90, GETDATE());

WITH doe_pubs as (
	select
		p.id,
		g.[funder-name]
	from Publication p
		join [Grant Publication Relationship] gpr
			on p.id = gpr.[Publication ID]
		join [grant] g
			on g.id = gpr.[Grant ID]
	where
		p.[Reporting Date 1] BETWEEN @ninety_days_ago AND GETDATE()
		and g.[funder-name] LIKE ('%USDOE%')
	group by
		p.id,
		g.[funder-name]
)
SELECT
	dp.id as [pub ID],
	CONCAT('https://oapolicy.universityofcalifornia.edu/viewobject.html?cid=1&id=', dp.id) as [Pub URL],
	dp.[funder-name],
	p.title,
	p.[Reporting Date 1],
	p.[publication-date],
	pr.id as [Pub Record ID],
	pr.[Data Source],
	pr.[Data Source Proprietary ID] as [Data Source ID],
	prf.Filename,
	prf.[File URL],
	CAST(p.[created when] as DATE) as [p.Created],
	CAST(pr.[Created When] as DATE) as [pr.Created],
	CAST(prf.[File First Uploaded Date] as DATE) as [File First Uploaded],
		DATEDIFF(
		day, p.[created when], pr.[Created When]
	) as [p.Created - pr.Created],
	DATEDIFF(
		day, p.[Reporting Date 1], pr.[Created When]
	) as [p.RD1 - pr Created],
	DATEDIFF(
		day, p.[Reporting Date 1], prf.[File First Uploaded Date]
	) as [p.RD1 - prf First]
FROM
	doe_pubs dp
		join Publication p
			on dp.id = p.id
		join [Publication Record] pr
			on p.id = pr.[Publication ID]
			and pr.[Data Source] != 'eScholarship'
		join [Publication record file] prf
			on pr.id = prf.[Publication Record ID]
 			and prf.[Index] = 0
order by
	pr.[Data Source],
	DATEDIFF(
		day, p.[Reporting Date 1], pr.[Created When]
	) asc;

COMMIT TRANSACTION;