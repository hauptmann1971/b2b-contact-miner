from sqlalchemy import text


def get_contact_type_counts(db):
    """Return contact type counters robustly for enum and legacy rows."""
    rows = db.execute(
        text(
            """
        SELECT LOWER(CAST(contact_type AS CHAR)) AS contact_type, COUNT(*) AS cnt
        FROM contacts
        GROUP BY LOWER(CAST(contact_type AS CHAR))
        """
        )
    ).mappings().all()
    counts = {row["contact_type"]: int(row["cnt"]) for row in rows}
    return {
        "email": counts.get("email", 0),
        "telegram": counts.get("telegram", 0),
        "linkedin": counts.get("linkedin", 0),
        "phone": counts.get("phone", 0),
    }
