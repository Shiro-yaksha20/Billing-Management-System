import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Staff, Service, Customer, Bill, BillItem

@pytest.fixture(scope="function")
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_bill_calculation(test_db_session):
    # Setup data
    customer = Customer(name="Charlie", phone="5555555555")
    staff = Staff(name="Dave", role="Barber")
    service1 = Service(name="Cut", price=100.0)
    service2 = Service(name="Shave", price=50.0)

    test_db_session.add_all([customer, staff, service1, service2])
    test_db_session.commit()

    # Create Bill
    bill = Bill(
        customer_id=customer.id,
        staff_id=staff.id,
        payment_method="Cash",
        bill_datetime=datetime.now()
    )

    # Add items
    item1 = BillItem(service_id=service1.id, quantity=1, unit_price=service1.price, line_total=100.0)
    item2 = BillItem(service_id=service2.id, quantity=2, unit_price=service2.price, line_total=100.0) # 2 * 50 = 100

    bill.items.append(item1)
    bill.items.append(item2)

    # Calculate totals logic (mimicking GUI logic)
    subtotal = sum(item.line_total for item in bill.items)
    bill.subtotal = subtotal # 200.0

    # Discount (Flat 20)
    bill.discount_type = "flat"
    bill.discount_amount = 20.0

    # Tax (10%)
    bill.tax_percent = 10.0

    taxable_amount = subtotal - bill.discount_amount # 180.0
    tax_amount = taxable_amount * (bill.tax_percent / 100) # 18.0
    bill.tax_amount = tax_amount
    bill.total = taxable_amount + tax_amount # 198.0

    test_db_session.add(bill)

    # Update customer last visit
    customer.last_visit_at = bill.bill_datetime

    test_db_session.commit()

    # Verify
    saved_bill = test_db_session.query(Bill).first()
    assert saved_bill.subtotal == 200.0
    assert saved_bill.discount_amount == 20.0
    assert saved_bill.tax_amount == 18.0
    assert saved_bill.total == 198.0

    saved_customer = test_db_session.query(Customer).first()
    assert saved_customer.last_visit_at == saved_bill.bill_datetime

def test_bill_calculation_percentage_discount(test_db_session):
    # Setup data
    customer = Customer(name="Eve", phone="666")
    staff = Staff(name="Frank", role="Stylist")
    service = Service(name="Color", price=200.0)

    test_db_session.add_all([customer, staff, service])
    test_db_session.commit()

    bill = Bill(customer_id=customer.id, staff_id=staff.id)
    item = BillItem(service_id=service.id, quantity=1, unit_price=service.price, line_total=200.0)
    bill.items.append(item)

    subtotal = 200.0
    bill.subtotal = subtotal

    # Discount (10%)
    bill.discount_type = "percent"
    bill.discount_amount = subtotal * 0.10 # 20.0

    # Tax (0%)
    bill.tax_percent = 0.0
    bill.tax_amount = 0.0

    bill.total = subtotal - bill.discount_amount # 180.0

    test_db_session.add(bill)
    test_db_session.commit()

    saved_bill = test_db_session.query(Bill).first()
    assert saved_bill.total == 180.0
