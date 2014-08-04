TICKETS_SOLD_BY_DAYS = """
SELECT DATE_FORMAT(p.purchase_date, '%%Y/%%m/%%d') AS 'purchase_date',
    COUNT(DISTINCT tc.id) AS 'ticket_count'
FROM texas_occurrence o
    INNER JOIN texas_purchase p ON p.occurrence_id = o.id
    INNER JOIN texas_ticket tc ON tc.purchase_id = p.id
WHERE o.id = %s
    AND p.status = 'P'
GROUP BY DATE_FORMAT(p.purchase_date, '%%Y/%%m/%%d')
ORDER BY p.purchase_date
"""

TICKETS_SOLD_BY_MONTH = """
SELECT DATE_FORMAT(p.purchase_date, '%%Y/%%m') AS 'purchase_month',
    COUNT(DISTINCT tc.id) AS 'ticket_count'
FROM texas_occurrence o
    INNER JOIN texas_purchase p ON p.occurrence_id = o.id
    INNER JOIN texas_ticket tc ON tc.purchase_id = p.id
WHERE o.id = %s
    AND p.status = 'P'
GROUP BY DATE_FORMAT(p.purchase_date, '%%Y/%%m')
ORDER BY p.purchase_date
"""

TICKETS_SOLD_BY_TIER = """
SELECT ti.label AS 'tier',
    COUNT(DISTINCT tc.id) AS 'ticket_count'
FROM texas_occurrence o
    INNER JOIN texas_purchase p ON p.occurrence_id = o.id
    INNER JOIN texas_ticket tc ON tc.purchase_id = p.id
    INNER JOIN texas_tier ti ON ti.id = tc.tier_id
WHERE o.id = %s
    AND p.status = 'P'
GROUP BY ti.label
ORDER BY ti.start_date
"""

USERS_BY_TICKET_COUNT = """
SELECT ticket_count AS 'tickets',
    COUNT(user_id) AS 'user_count'
FROM (
SELECT COUNT(tc.id) AS 'ticket_count',
    p.user_id
FROM texas_occurrence o
    INNER JOIN texas_purchase p ON p.occurrence_id = o.id
    INNER JOIN texas_ticket tc ON tc.purchase_id = p.id
WHERE o.id = %s
    AND p.status = 'P'
GROUP BY p.user_id
) AS a
GROUP BY a.ticket_count
ORDER BY a.ticket_count
"""

AVG_TICKETS_BY_TIER = """
SELECT ti.label AS 'tier',
    COUNT(DISTINCT tc.id) / COUNT(DISTINCT p.id) AS 'avg_tickets'
FROM texas_occurrence o
    INNER JOIN texas_purchase p ON p.occurrence_id = o.id
    INNER JOIN texas_ticket tc ON tc.purchase_id = p.id
    INNER JOIN texas_tier ti ON ti.id = tc.tier_id
WHERE o.id = %s
    AND p.status = 'P'
GROUP BY ti.label
ORDER BY ti.start_date
"""
