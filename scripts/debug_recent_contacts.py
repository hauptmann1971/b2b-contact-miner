#!/usr/bin/env python3
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from sqlalchemy import desc  # noqa: E402

from models.database import Contact, DomainContact, SessionLocal  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        n_contact = db.query(Contact).count()
        n_dc = db.query(DomainContact).count()
        print(f"contacts table rows: {n_contact}")
        print(f"domain_contacts rows: {n_dc}")

        rows_from_json = 0
        for d in db.query(DomainContact).order_by(desc(DomainContact.created_at)).limit(20):
            p = d.contacts_json or {}
            if not isinstance(p, dict):
                continue
            has = bool(
                (p.get("emails") or p.get("telegram") or p.get("linkedin"))
                or (
                    isinstance(p.get("social"), dict)
                    and any(p.get("social", {}).values())
                )
            )
            if has:
                rows_from_json += 1
            print(f"  dc id={d.id} domain={d.domain!r} json_has_data={has} json={p!r:.120}")

        recent = (
            db.query(Contact, DomainContact)
            .join(DomainContact, Contact.domain_contact_id == DomainContact.id)
            .order_by(desc(Contact.created_at))
            .limit(5)
            .all()
        )
        print(f"recent from contacts table: {len(recent)} sample")
        for c, d in recent:
            print(f"  {c.contact_type} {c.value!r} @ {d.domain}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
