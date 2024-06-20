import pytest
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Field, Session, SQLModel, create_engine, delete
from sqlmodel.pool import StaticPool

from djene.queryset import DjQuery


@pytest.fixture(scope="function")
def engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def session(engine):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            soldiers = [
                Soldier(id=1, name="Cloud Strife", rank="1st Class"),
                Soldier(id=2, name="Zack Fair", rank="1st Class"),
                Soldier(id=3, name="Sephiroth", rank="1st Class"),
                Soldier(id=4, name="Tifa Lockhart"),  # No rank (civilian)
                Soldier(id=5, name="Aerith Gainsborough"),  # No rank (Ancient)
            ]
            session.add_all(soldiers)

            yield session
        finally:
            session.rollback()


class Soldier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    rank: str | None = None  # Optional rank


def test_filtering(session):
    # Find all 1st Class Soldiers
    first_class_soldiers = DjQuery(Soldier, session).filter(rank="1st Class").all()
    assert len(first_class_soldiers) == 3
    for soldier in first_class_soldiers:
        assert soldier.rank == "1st Class"


def test_ordering(session):
    # Order Soldiers alphabetically by name
    soldiers = DjQuery(Soldier, session).order_by("name").all()

    # breakpoint()

    assert [soldier.name for soldier in soldiers] == [
        "Aerith Gainsborough",
        "Cloud Strife",
        "Sephiroth",
        "Tifa Lockhart",
        "Zack Fair",
    ]


def test_get(session):
    cloud = DjQuery(Soldier, session).get(id=1)
    assert cloud.name == "Cloud Strife"


def test_retrieval(session):
    # Get first and last
    first_soldier = DjQuery(Soldier, session).first()
    assert first_soldier.name == "Cloud Strife"

    # last_soldier = DjQuery(Soldier, session).last()
    # assert last_soldier.name == "Aerith Gainsborough"


def test_get_or_none(session):
    # Existing Soldier
    zack = DjQuery(Soldier, session).get_or_none(id=2)
    assert zack.name == "Zack Fair"

    # Non-existent Soldier
    genesis = DjQuery(Soldier, session).get_or_none(id=999)
    assert genesis is None


def test_limit_and_offset(session):
    limited_soldiers = DjQuery(Soldier, session).limit(2).all()
    assert len(limited_soldiers) == 2

    # Combine limit and offset
    offset_soldiers = DjQuery(Soldier, session).offset(2).limit(2).all()
    assert len(offset_soldiers) == 2
    assert offset_soldiers[0].name == "Sephiroth"


def test_all(session):
    # Count all Soldiers
    soldier_count = len(DjQuery(Soldier, session).all())
    assert soldier_count == 5


def test_get_multiple_results(session):
    with pytest.raises(MultipleResultsFound):
        results = DjQuery(Soldier, session).get(rank="1st Class")
        print(results)


def test_get_no_results(session):
    with pytest.raises(NoResultFound):
        DjQuery(Soldier, session).get(name="Genesis Rhapsodos")
