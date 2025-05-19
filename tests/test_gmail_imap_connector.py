import pytest
from unittest.mock import patch, MagicMock
import imaplib
from src.connectors.gmail_connector import GmailConnector

@pytest.fixture
def test_email():
    return "test@gmail.com"

@pytest.fixture
def test_token():
    return "fake_access_token"

@pytest.fixture
def mock_token_provider(test_token):
    provider = MagicMock(return_value=test_token)
    return provider

@pytest.fixture
def connector(test_email, mock_token_provider):
    return GmailConnector(
        user_email=test_email,
        access_token_provider=mock_token_provider
    )

def test_successful_connection(connector, mock_token_provider):
    """Test successful connection to Gmail IMAP server."""
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        # Arrange
        mock_imap_instance = MagicMock()
        mock_imap.return_value = mock_imap_instance
        mock_imap_instance.authenticate.return_value = ('OK', [b'Success'])

        # Act
        result = connector.connect()

        # Assert
        assert result is True
        mock_imap.assert_called_once_with('imap.gmail.com', 993)
        mock_imap_instance.authenticate.assert_called_once()
        assert connector.imap_server == mock_imap_instance
        mock_token_provider.assert_called_once()

def test_authentication_failure(connector):
    """Test connection failure due to authentication error."""
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        # Arrange
        mock_imap_instance = MagicMock()
        mock_imap.return_value = mock_imap_instance
        mock_imap_instance.authenticate.return_value = ('NO', [b'Authentication failed'])

        # Act & Assert
        with pytest.raises(ConnectionError) as exc_info:
            connector.connect()
        
        assert 'XOAUTH2 authentication failed' in str(exc_info.value)
        assert connector.imap_server is None

def test_imap_error(connector):
    """Test connection failure due to IMAP error."""
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        # Arrange
        mock_imap.side_effect = imaplib.IMAP4.error('Connection refused')

        # Act & Assert
        with pytest.raises(ConnectionError) as exc_info:
            connector.connect()
        
        assert 'Failed to connect to Gmail IMAP' in str(exc_info.value)
        assert connector.imap_server is None

def test_disconnect(connector):
    """Test proper disconnection."""
    # Arrange
    mock_imap = MagicMock()
    connector.imap_server = mock_imap

    # Act
    connector.disconnect()

    # Assert
    mock_imap.logout.assert_called_once()
    assert connector.imap_server is None

def test_context_manager(test_email, mock_token_provider):
    """Test the connector as a context manager."""
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_imap_instance = MagicMock()
        mock_imap.return_value = mock_imap_instance
        mock_imap_instance.authenticate.return_value = ('OK', [b'Success'])

        with GmailConnector(test_email, mock_token_provider) as connector:
            assert connector.user_email == test_email
            assert connector.imap_server is not None

        # Assert disconnect was called when exiting context
        mock_imap_instance.logout.assert_called_once() 