SET TRANSACTION ISOLATION LEVEL SNAPSHOT
BEGIN TRANSACTION;

DECLARE @time_window AS DATE = DATEADD(day,-90, GETDATE());

DECLARE @fiscal_year_cutoff date =
	CASE WHEN (MONTH(GETDATE()) >= 10)
        THEN CONVERT(VARCHAR, YEAR(GETDATE()) - 3) + '-10-01'
        ELSE CONVERT(VARCHAR, YEAR(GETDATE()) - 2) + '-10-01'
	END;

-- Narrow down the pool of publications to:
-- The publication window; Only pubs with file deposits.
with relevant_pubs as (
	select
		distinct p.id as [Publication ID],
		pp.ID as [Pending Publication ID],
		pr.[Data Source],
		pr.[Created When] as 'Record Created When',
		pr.[Data Source Proprietary ID],
		prf.[File URL],
		eschol_pr.[oa-location-url]
	from
		[Pending Publication] pp
			full outer join [Publication] p
				on pp.[Publication ID] = p.ID
			join [Publication Record] pr
				on (
					p.id = pr.[Publication ID]
					or pp.[Publication ID] = pr.[Publication ID]
				) and p.id not in (
					select pr.[Publication ID]
					from [Publication Record] pr
						join [Publication Record File] prf
							on pr.ID = prf.[Publication Record ID]
							and pr.[Data Source] = 'eScholarship'
				)
			join [Publication record file] prf
				on pr.id = prf.[Publication Record ID]
 				and prf.[Index] = 0
 			left join [Publication Record] eschol_pr
 				on eschol_pr.[Publication ID] = p.id
 				and eschol_pr.[oa-location-url] is not null
	where
		(	p.[Reporting Date 1] > @fiscal_year_cutoff
			or p.[publication-date] > @fiscal_year_cutoff)
		and pr.[Created When] >= @time_window
	group by
		p.id,
		pp.ID,
		pr.[Data Source],
		pr.[Created When],
		pr.[Data Source Proprietary ID],
		prf.[File URL],
		eschol_pr.[oa-location-url]
),
claimed_rp as (
	select
		distinct rp.[Publication ID],
		STRING_AGG(
			case
				when claimed_u.[Primary Group Descriptor] like('%-lbl-%')
					THEN CONCAT('(Joint) ', claimed_u.[Computed Name Full])
				else claimed_u.[Computed Name Full]
			end
			, '; '
		) as [LBL Authors]
	from
		relevant_pubs rp
			join [Publication User Relationship] pur
				on rp.[Publication ID] = pur.[Publication ID]
			join [User] claimed_u
				on claimed_u.id = pur.[User ID]
				and claimed_u.[Primary Group Descriptor] like ('%lbl-%')
	group by
		rp.[Publication ID]
),
pending_rp as (
	select
		distinct rp.[Publication ID],
		STRING_AGG(
			case
				when pending_u.[Primary Group Descriptor] like('%-lbl-%')
					THEN CONCAT('(Joint) ', pending_u.[Computed Name Full])
				else pending_u.[Computed Name Full]
			end
			, '; '
		) as [LBL Authors]
	from
		relevant_pubs rp
			join [Pending Publication] pp
				on rp.[Pending Publication ID] = pp.ID
			join [User] pending_u
				on pp.[User ID] = pending_u.ID
				and pending_u.[Primary Group Descriptor] like ('%lbl-%')
	group by
		rp.[Publication ID]
)
select
	distinct rp.[Publication ID],
	CONCAT('https://oapolicy.universityofcalifornia.edu/viewobject.html?cid=1&id=',rp.[Publication ID]) as [Elements URL],
	p.[Title],
	p.[doi],
	p.[Type],
	rp.[Data Source],
	rp.[Data Source Proprietary ID],
	rp.[File URL],
	rp.[oa-location-url],
	claimed_rp.[LBL Authors] as [Claimed LBL authors],
	pending_rp.[LBL Authors] as [Pending LBL authors],
	case
		WHEN claimed_rp.[LBL Authors] is not null
		then 'claimed' else 'pending'
	end as 'LBL user claim status',
	p.[Reporting Date 1],
	p.[publication-date],
	rp.[Record Created When],
	p.[created when] as [Pub Created When]
from
	relevant_pubs rp
		join [Publication] p
			on rp.[Publication ID] = p.ID
		left join claimed_rp
			on rp.[Publication ID] = claimed_rp.[Publication ID]
		left join pending_rp
			on rp.[Publication ID] = pending_rp.[Publication ID]
where
	claimed_rp.[LBL Authors] is not null
	or pending_rp.[LBL Authors] is not null
order by
	p.[Type],
	'LBL user claim status',
	p.[Reporting Date 1] asc,
	rp.[Publication ID];