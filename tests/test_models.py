import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Staff, Service, Customer
from app import database

# Setup in-memory database for testing
@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override the real db_session to use our test session
    # However, since db_session is a context manager using SessionLocal,
    # we might need to patch it or just use the session directly for model tests.
    # For model tests, we will just use the session directly.

    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)

def test_create_staff(test_db):
    staff = Staff(name="Alice", phone="1234567890", active=True)
    test_db.add(staff)
    test_db.commit()

    retrieved = test_db.query(Staff).filter_by(name="Alice").first()
    assert retrieved is not None
    assert retrieved.phone == "1234567890"
    assert retrieved.active is True

def test_create_service(test_db):
    service = Service(name="Haircut", price=500.0, active=True)
    test_db.add(service)
    test_db.commit()

    retrieved = test_db.query(Service).filter_by(name="Haircut").first()
    assert retrieved is not None
    assert retrieved.price == 500.0

def test_create_customer(test_db):
    customer = Customer(name="Bob", phone="0987654321")
    test_db.add(customer)
    test_db.commit()

    retrieved = test_db.query(Customer).filter_by(name="Bob").first()
    assert retrieved is not None
    assert retrieved.phone == "0987654321"
