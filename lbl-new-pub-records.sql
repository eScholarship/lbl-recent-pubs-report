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
			and u.[Primary Group Descriptor] like ('%lbl%')
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
			and u.[Primary Group Descriptor] like ('%lbl%')
	where
		p.[Reporting Date 1] > @fiscal_year_cutoff
		or p.[publication-date] > @fiscal_year_cutoff
	group by
		p.id
)
select
	distinct p.id as [Elements ID],
	CONCAT('https://oapolicy.universityofcalifornia.edu/viewobject.html?cid=1&id=', p.id) as elements_url,
	prf.[File URL],
	p.title,
	case
		WHEN p.id in (select ID from claimed_lbl_pubs) THEN 'claimed'
		ELSE 'pending'
	end as 'LBL user claim status',
	clp.author_names as 'Claimed LBL Authors',
	plp.author_names as 'Pending LBL Authors',
	pr.[Data Source],
	pr.[Data Source Proprietary ID] as [Data Source ID],
	p.[Reporting Date 1],
	p.[publication-date],
	CAST(p.[created when] as DATE) as [Pub Created],
	CAST(pr.[Created When] as DATE) as [Pub Record Created]
from
	publication p
		join [Publication Record] pr
			on p.id = pr.[Publication ID]
			and p.id not in (
				select pr.[Publication ID]
				from [Publication Record] pr
				where pr.[Data Source] = 'eScholarship'
			)
		join [Publication record file] prf
			on pr.id = prf.[Publication Record ID]
 			and prf.[Index] = 0
 		join [Publication User Relationship] pur
 			on p.id = pur.[Publication ID]
 		left join pending_lbl_pubs plp
			on p.id = plp.ID
 		left join claimed_lbl_pubs clp
 			on p.id = clp.ID
WHERE
	pr.[Created When] BETWEEN @time_window AND GETDATE()
	AND (
		p.id in (select ID from pending_lbl_pubs)
		or p.id in (select ID from claimed_lbl_pubs)
	)
order by
	p.id;

COMMIT TRANSACTION;