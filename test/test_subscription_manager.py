import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from spade_fiware_artifacts.context_broker_suscription_manager import SubscriptionManagerArtifact


@pytest.fixture
def subscription_config():
    """Basic configuration for subscription tests"""
    return {
        "entity_type": "TestDevice",
        "entity_id": "test001",
        "watched_attributes": ["temperature", "humidity"],
        "context": ["https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"],
        "subscription_identifier": "test_sub_001"
    }


@pytest.fixture
def subscription_manager(subscription_config):
    """Basic SubscriptionManagerArtifact fixture with minimal mocking"""
    with patch('spade_fiware_artifacts.context_broker_suscription_manager.spade_artifact.Artifact'):
        artifact = SubscriptionManagerArtifact(
            jid="test@example.com",
            passwd="password",
            config=subscription_config,
            broker_url="http://localhost:9090"
        )
        artifact.presence = MagicMock()
        return artifact


class TestSubscriptionManagerBasics:
    """Test basic functionality of SubscriptionManagerArtifact"""

    def test_initialization(self, subscription_manager, subscription_config):
        """Test proper initialization of the artifact"""
        assert subscription_manager.broker_url == "http://localhost:9090"
        assert subscription_manager.config['watched_attributes'] == subscription_config["watched_attributes"]
        assert isinstance(subscription_manager.recent_notifications, dict)
        assert isinstance(subscription_manager.active_subscriptions, dict)

    def test_generate_subscription_id(self, subscription_manager):
        """Test subscription ID generation"""
        sub_id = subscription_manager.generate_subscription_id()
        assert sub_id.startswith("sub_")
        assert len(sub_id) == 12  # "sub_" + 8 chars

    def test_format_entity_id(self, subscription_manager):
        """Test entity ID formatting"""
        # Test with plain ID
        entity_id = subscription_manager.format_entity_id("Device", "dev001")
        assert entity_id == "urn:ngsi-ld:Device:dev001"

        # Test with already formatted ID
        formatted_id = "urn:ngsi-ld:Device:dev001"
        entity_id = subscription_manager.format_entity_id("Device", formatted_id)
        assert entity_id == formatted_id






class TestSubscriptionCreation:
    """Test subscription creation and related functionality"""

    @pytest.mark.asyncio
    async def test_build_subscription_data(self, subscription_manager):
        """Test subscription data building"""
        local_ip = "192.168.1.1"
        sub_id = "test_sub_001"

        subscription_data = subscription_manager.build_subscription_data(local_ip, sub_id)

        assert subscription_data["type"] == "Subscription", "Tipo de suscripción incorrecto"
        assert subscription_data["entities"][0]["type"] == "TestDevice", "Tipo de entidad incorrecto"
        assert subscription_data["notification"]["endpoint"]["uri"].startswith(
            "http://"), "URI de notificación mal formada"
        assert "temperature" in subscription_data["watchedAttributes"], "Falta atributo temperature"
        assert "humidity" in subscription_data["watchedAttributes"], "Falta atributo humidity"
        assert sub_id in subscription_data["description"], "ID de suscripción no encontrado en la descripción"

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, subscription_manager):
        """Test successful subscription creation"""
        sub_data = {
            "type": "Subscription",
            "entities": [{"type": "TestDevice"}],
            "notification": {
                "endpoint": {
                    "uri": "http://localhost:8000/notify",
                    "accept": "application/json"
                }
            }
        }

        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.headers = {"Location": "urn:ngsi-ld:Subscription:123"}

        class MockSession:
            def __init__(self):
                self.post_calls = []

            @asynccontextmanager
            async def post(self, url, **kwargs):
                self.post_calls.append((url, kwargs))
                yield mock_response

        mock_session = MockSession()

        sub_id = await subscription_manager.create_subscription(
            mock_session,
            sub_data,
            "test_sub_001"
        )

        assert len(mock_session.post_calls) == 1, "El método post debería haber sido llamado una vez"
        assert sub_id == "urn:ngsi-ld:Subscription:123", "ID de suscripción incorrecto"

        assert "test_sub_001" in subscription_manager.active_subscriptions, "Suscripción no guardada en active_subscriptions"
        assert subscription_manager.active_subscriptions[
                   "test_sub_001"] == "urn:ngsi-ld:Subscription:123", "ID guardado incorrecto"

        url, kwargs = mock_session.post_calls[0]
        assert url == f"{subscription_manager.broker_url}/ngsi-ld/v1/subscriptions", "URL incorrecta"
        assert kwargs["headers"]["Content-Type"] == "application/ld+json", "Content-Type incorrecto"
        assert kwargs["json"] == sub_data, "Datos de suscripción incorrectos"




class TestNotificationHandling:
    """Test notification handling functionality"""

    @pytest.mark.asyncio
    async def test_handle_notification_success(self, subscription_manager):
        """Test successful notification handling"""
        subscription_manager.publish = AsyncMock()

        notification_data = {
            "notifiedAt": "2024-01-01T12:00:00Z",
            "data": [{
                "id": "urn:ngsi-ld:TestDevice:test001",
                "type": "TestDevice",
                "temperature": {"value": 25.0},
                "humidity": {"value": 60}
            }]
        }

        request = MagicMock()
        request.json = AsyncMock(return_value=notification_data)

        response = await subscription_manager.handle_notification(request)

        assert response.status == 200
        assert "urn:ngsi-ld:TestDevice:test001" in subscription_manager.recent_notifications
        subscription_manager.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_notification_invalid_json(self, subscription_manager):
        """Test notification handling with invalid JSON"""
        request = MagicMock()
        request.json = AsyncMock(side_effect=json.JSONDecodeError('Invalid JSON', '', 0))

        response = await subscription_manager.handle_notification(request)
        assert response.status == 400


from unittest.mock import patch, AsyncMock
import pytest
import aiohttp
from contextlib import asynccontextmanager


class TestSubscriptionManagement:
    @pytest.mark.asyncio
    async def test_get_active_subscriptions(self, subscription_manager):
        """Test retrieving active subscriptions"""
        test_data = [{
            "id": "urn:ngsi-ld:Subscription:123",
            "type": "Subscription",
            "description": f"Artifact-ID: {subscription_manager.jid}, Sub-ID: test_sub_001"
        }]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=test_data)

        class MockSession:
            def __init__(self):
                self.get_calls = []

            @asynccontextmanager
            async def get(self, url, **kwargs):
                self.get_calls.append((url, kwargs))
                yield mock_response

        mock_session = MockSession()

        subscriptions = await subscription_manager.get_active_subscriptions(mock_session)

        # Verificaciones
        assert len(mock_session.get_calls) == 1
        assert len(subscriptions) == 1
        assert subscriptions[0]["id"] == "urn:ngsi-ld:Subscription:123"

        url, kwargs = mock_session.get_calls[0]
        assert url == f"{subscription_manager.broker_url}/ngsi-ld/v1/subscriptions"
        assert kwargs["headers"]["Accept"] == "application/ld+json"
class TestNetworkUtilities:
    """Test network-related utility functions"""

    def test_get_local_ip(self, subscription_manager):
        """Test local IP address retrieval"""
        ip = subscription_manager.get_local_ip()
        assert isinstance(ip, str)
        # Should be either a valid IP or localhost
        assert ip == "127.0.0.1" or len(ip.split(".")) == 4

    def test_find_free_port(self, subscription_manager):
        """Test free port finding"""
        port = subscription_manager.find_free_port()
        assert isinstance(port, int)
        assert 8000 <= port <= 65000


class TestCleanup:
    """Test cleanup functionality"""

    @pytest.mark.asyncio
    async def test_cleanup(self, subscription_manager):
        """Test cleanup process"""
        subscription_manager.delete_artifact_subscriptions = AsyncMock()
        await subscription_manager.cleanup()
        subscription_manager.delete_artifact_subscriptions.assert_called_once()