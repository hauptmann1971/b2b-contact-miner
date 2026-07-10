from sqlalchemy import text


def get_recent_contacts(db, tenant_id: int, limit: int = 20):
    rows = db.execute(
        text(
            """
        SELECT LOWER(CAST(c.contact_type AS CHAR)) AS contact_type,
               c.value,
               dc.domain AS domain,
               c.created_at
        FROM contacts c
        JOIN domain_contacts dc ON dc.id = c.domain_contact_id
        WHERE c.tenant_id = :tenant_id
        ORDER BY c.created_at DESC
        LIMIT :limit
        """
        ),
        {"tenant_id": tenant_id, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def get_contact_type_counts(db, tenant_id: int):
    rows = db.execute(
        text(
            """
        SELECT LOWER(CAST(contact_type AS CHAR)) AS contact_type, COUNT(*) AS cnt
        FROM contacts
        WHERE tenant_id = :tenant_id
        GROUP BY LOWER(CAST(contact_type AS CHAR))
        """
        ),
        {"tenant_id": tenant_id},
    ).mappings().all()
    counts = {row["contact_type"]: int(row["cnt"]) for row in rows}
    return {
        "email": counts.get("email", 0),
        "telegram": counts.get("telegram", 0),
        "linkedin": counts.get("linkedin", 0),
        "phone": counts.get("phone", 0),
    }
