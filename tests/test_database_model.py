import os
import sys

from sqlalchemy.dialects import mysql

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_contact_type_enum_binds_lowercase_values_for_mysql():
    from models.database import Contact, ContactType

    enum_type = Contact.__table__.c.contact_type.type

    assert enum_type.enums == [
        "email",
        "telegram",
        "linkedin",
        "phone",
        "x",
        "facebook",
        "instagram",
        "youtube",
    ]

    bind_processor = enum_type.bind_processor(mysql.dialect())
    assert bind_processor(ContactType.EMAIL) == "email"
