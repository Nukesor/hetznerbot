-- New offers by weekday and hour of day.
--
-- Only includes offers first seen after 2026-06-13 11:49, as that's when the change
-- was deployed to the hetznerbot

SELECT
    EXTRACT(ISODOW FROM first_seen_at)::int AS iso_weekday,
    TO_CHAR(first_seen_at, 'Dy') AS weekday,
    EXTRACT(HOUR FROM first_seen_at)::int AS hour_of_day,
    COUNT(*) AS new_offer_count
FROM offer
WHERE deactivated IS FALSE
  AND first_seen_at > TIMESTAMPTZ '2026-06-13T11:49:21+00:00'
GROUP BY 1, 2, 3
ORDER BY 1, 3;
