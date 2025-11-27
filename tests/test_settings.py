import pytest
from app import settings_service
from app.models import Base, Setting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

# Mock keyring
@pytest.fixture(autouse=True)
def mock_keyring(mocker):
    secrets = {}

    def get_password(service_name, username):
        return secrets.get(username)

    def set_password(service_name, username, password):
        secrets[username] = password

    def delete_password(service_name, username):
        if username in secrets:
            del secrets[username]

    mocker.patch('app.settings_service.keyring.get_password', side_effect=get_password)
    mocker.patch('app.settings_service.keyring.set_password', side_effect=set_password)
    mocker.patch('app.settings_service.keyring.delete_password', side_effect=delete_password)
    return secrets

# Mock db_session in settings_service to use our test DB
@pytest.fixture(autouse=True)
def mock_db_session(mocker, test_db_session):
    # Context manager mock
    class MockSessionContext:
        def __enter__(self):
            return test_db_session
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    mocker.patch('app.settings_service.db_session', side_effect=MockSessionContext)

def test_get_set_setting(test_db_session):
    # Test defaults
    assert settings_service.get_setting("non_existent", "default") == "default"
    assert settings_service.get_setting("non_existent") is None

    # Test set and get
    settings_service.set_setting("app_theme", "Dark")
    assert settings_service.get_setting("app_theme") == "Dark"

    # Test update
    settings_service.set_setting("app_theme", "Light")
    assert settings_service.get_setting("app_theme") == "Light"

    # Verify directly in DB
    setting = test_db_session.query(Setting).filter_by(key="app_theme").first()
    assert setting.value == "Light"

def test_get_set_secret(mock_keyring):
    # Test set
    settings_service.set_secret("api_key", "12345")
    assert mock_keyring["api_key"] == "12345"

    # Test get
    assert settings_service.get_secret("api_key") == "12345"

    # Test nonexistent
    assert settings_service.get_secret("missing") is None

    # Test delete (value=None) - assuming implementation handles it, checking code...
    # The code says: "If None, the secret is deleted." - wait, let's check code again.
    # Yes: keyring.delete_password
    settings_service.set_secret("api_key", None)
    assert "api_key" not in mock_keyring
