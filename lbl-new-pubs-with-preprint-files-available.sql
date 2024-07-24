SET TRANSACTION ISOLATION LEVEL SNAPSHOT
BEGIN TRANSACTION;

DECLARE @time_window AS DATE = DATEADD(day,-90, GETDATE());

DECLARE @fiscal_year_cutoff date =
	CASE WHEN (MONTH(GETDATE()) >= 10)
        THEN CONVERT(VARCHAR, YEAR(GETDATE()) - 3) + '-10-01'
        ELSE CONVERT(VARCHAR, YEAR(GETDATE()) - 2) + '-10-01'
	END;

with pending_lbl_pubs as (
	SELECT
		distinct pp.[Publication ID] as ID,
		STRING_AGG(
			case
				when u.[Primary Group Descriptor] like('%-lbl-%')
					THEN CONCAT('(Joint) ', u.[Computed Name Full])
				else u.[Computed Name Full]
			end
			, '; '
		) as [author_names]
	FROM [Pending Publication] pp
		join
			[Publication] p on pp.[Publication ID] = p.id
		join [User] u
			on pp.[User ID] = u.id
			and u.[Primary Group Descriptor] like ('%lbl-%')
	where
		p.[Reporting Date 1] > @fiscal_year_cutoff
		or p.[publication-date] > @fiscal_year_cutoff
	group by
		pp.[Publication ID]

),
claimed_lbl_pubs as (
	select
		distinct p.ID,
		STRING_AGG(
			case
				when u.[Primary Group Descriptor] like('%-lbl-%')
					THEN CONCAT('(Joint) ', u.[Computed Name Full])
				else u.[Computed Name Full]
			end
			, '; '
		) as author_names
	from Publication p
		join [Publication User Relationship] pur
			on p.id = pur.[Publication ID]
		join [User] u
			on u.id = pur.[User ID]
			and u.[Primary Group Descriptor] like ('%lbl-%')
	where
		p.[Reporting Date 1] > @fiscal_year_cutoff
		or p.[publication-date] > @fiscal_year_cutoff
	group by
		p.id
)
select
	distinct p.id as [New Pub ID],
	CONCAT('https://oapolicy.universityofcalifornia.edu/viewobject.html?cid=1&id=',p.id) as [New Pub URL],
	p.title,
	ppr.[Reversed Type] as [Relationship],
	ppr.[Publication 1 ID] as [Preprint Pub ID],
	CONCAT('https://oapolicy.universityofcalifornia.edu/viewobject.html?cid=1&id=',ppr.[Publication 1 ID]) as [Preprint Pub URL],
	related_pr.[Data Source] as [Preprint Data Source],
	prf.[File URL] as [Preprint file URL],
	max(pub_pr.[oa-location-url]) as [New pub OA location],
	clp.author_names as 'Claimed LBL Authors',
	plp.author_names as 'Pending LBL Authors',
	CONVERT(date, p.[Created When]) as [New Pub Created],
	p.[Reporting Date 1] as [New Pub RD1],
	p.[publication-date] as [New Pub Publication Date]
from [Publication] p
	full outer join [Pending Publication] pp
		on p.id = pp.[Publication ID]
	join [Publication Record] pub_pr
		on p.id = pub_pr.[Publication ID]
	join [Publication Publication Relationship] ppr
		on p.id = ppr.[Publication 2 ID]
		or pp.[Publication ID] = ppr.[Publication 2 ID]
	join [Publication Record] related_pr
		on ppr.[Publication 1 ID] = related_pr.[Publication ID]
	join [Publication Record File] prf
		on related_pr.ID = prf.[Publication Record ID]
		and prf.[Index] =0
	left join pending_lbl_pubs plp
		on p.id = plp.ID
	left join claimed_lbl_pubs clp
		on p.id = clp.ID
where
	p.[Created When] > @time_window
	and p.id not in (
		select distinct pr.[Publication ID]
		from [Publication Record] pr
			join [Publication Record File] prf
				on pr.id = prf.[Publication Record ID]
	) and (
		p.id in (select ID from pending_lbl_pubs)
		or p.id in (select ID from claimed_lbl_pubs)
	)
group by
	p.id,
	p.title,
	ppr.[Reversed Type],
	ppr.[Publication 1 ID],
	related_pr.[Data Source],
	prf.[File URL],
	clp.author_names,
	plp.author_names,
	p.[Created When],
	p.[Reporting Date 1],
	p.[publication-date];