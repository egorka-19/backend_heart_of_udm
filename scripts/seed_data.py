"""
Seed PostgreSQL with event categories, events, and sample routes.
Run from backend/: python scripts/seed_data.py
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.event import Event, EventCategory  # noqa: E402
from app.models.route import Route  # noqa: E402


def seed(db: Session) -> None:
    if db.execute(select(EventCategory.id).limit(1)).first():
        print("Already seeded, skip.")
        return

    cats = [
        EventCategory(id=uuid.uuid4(), name="Все события", type="all", sort_order=0),
        EventCategory(id=uuid.uuid4(), name="Театр", type="Театр", sort_order=10),
        EventCategory(id=uuid.uuid4(), name="Музей", type="Музей", sort_order=20),
        EventCategory(id=uuid.uuid4(), name="Парк", type="Парк", sort_order=30),
        EventCategory(id=uuid.uuid4(), name="Ресторан", type="Ресторан", sort_order=40),
    ]
    for c in cats:
        db.add(c)

    events_data = [
        ("Робин Гуд", "Театр", "Русский драматический театр Удмуртии"),
        ("Любовь и голуби", "Театр", "ДК «Аксион»"),
        ("Panorama", "Ресторан", "Открыт до 23:00"),
        ("Музей ИЖМАШ", "Музей", "ул. Свердлова, 32"),
        ("Парк имени С. М. Кирова", "Парк", "Открыт до 23:00"),
    ]
    for name, typ, desc in events_data:
        e = Event(
            id=uuid.uuid4(),
            legacy_name=name,
            name=name,
            description=desc,
            type=typ,
            age="0+",
            schedule="пн-вс 10:00–20:00",
            place="Ижевск",
            maps_url="https://yandex.ru/maps/",
        )
        db.add(e)

    # Sample routes (categories align with PlusFragment UI)
    routes = [
        Route(
            id=uuid.uuid4(),
            name="Старый и Новый Ижевск",
            description="Познавательный маршрут по историческим местам города",
            category="С детьми",
            goal="Экскурсия",
            days_range="1",
            people_count="2-4",
            duration="3 часа",
            difficulty="Легкий",
        ),
        Route(
            id=uuid.uuid4(),
            name="Вечерний Ижевск",
            description="Романтическая прогулка",
            category="Романтические",
            goal="Отдых",
            days_range="1",
            people_count="2",
            duration="2 часа",
            difficulty="Легкий",
        ),
        Route(
            id=uuid.uuid4(),
            name="Исторический центр",
            description="Экскурсия по историческим местам",
            category="Исторические",
            goal="Экскурсия",
            days_range="2-3",
            people_count="1-10",
            duration="6 часов",
            difficulty="Средний",
        ),
        # Recommended buckets by user category from chat
        Route(
            id=uuid.uuid4(),
            name="IT-маршрут Ижевска",
            description="Технологии и промышленность",
            category="IT",
            goal="Экскурсия",
            days_range="1",
            people_count="1-5",
            duration="4 часа",
            difficulty="Легкий",
        ),
    ]
    for r in routes:
        db.add(r)

    db.commit()
    print("Seed done.")


if __name__ == "__main__":
    s = SessionLocal()
    try:
        seed(s)
    finally:
        s.close()
