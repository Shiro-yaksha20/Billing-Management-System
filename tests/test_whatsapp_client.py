import pytest
from app import whatsapp_client

def test_send_whatsapp_message_no_credentials(mocker):
    # Mock settings to return None for token/phone_id
    mocker.patch('app.settings_service.get_secret', return_value=None)
    mocker.patch('app.settings_service.get_setting', return_value=None)

    # Mock logger to ensure no crash
    mocker.patch('app.whatsapp_client.logger')

    success, response = whatsapp_client.send_whatsapp_message("123", "Hello")

    assert success is False
    assert "not configured" in response.get("error", "")

def test_send_whatsapp_message_success(mocker):
    # Mock settings
    mocker.patch('app.settings_service.get_secret', return_value="fake_token")
    mocker.patch('app.settings_service.get_setting', side_effect=lambda k, d=None: "fake_phone_id" if k == "whatsapp_phone_id" else d)

    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    success, response = whatsapp_client.send_whatsapp_message("123", "Hello")

    assert success is True
    assert response == {"status": "success"}

    # Verify call arguments
    args, kwargs = mock_post.call_args
    assert "https://graph.facebook.com/v15.0/fake_phone_id/messages" in args[0]
    assert kwargs['headers']['Authorization'] == "Bearer fake_token"

def test_send_whatsapp_message_attachment_missing(mocker):
    mocker.patch('app.settings_service.get_secret', return_value="fake_token")
    mocker.patch('app.settings_service.get_setting', return_value="fake_phone_id")
    mocker.patch('os.path.exists', return_value=False)

    success, response = whatsapp_client.send_whatsapp_message("123", "Hello", attachment_path="/tmp/missing.pdf")

    assert success is False
    assert "not found" in response.get("error", "")
