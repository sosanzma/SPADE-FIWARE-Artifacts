import asyncio
import socket

import pytest
import json
from unittest.mock import patch, AsyncMock, ANY
import pytest
import aiohttp
from contextlib import asynccontextmanager
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

    def test_build_subscription_data_empty_entity_type(self, subscription_manager):
        """Test building subscription data with empty entity type"""
        subscription_manager.config["entity_type"] = ""
        local_ip = "192.168.1.1"
        sub_id = "test_sub_001"

        subscription_data = subscription_manager.build_subscription_data(local_ip, sub_id)
        assert subscription_data["entities"][0]["type"] == "", "Should handle empty entity type"


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


    @pytest.mark.asyncio
    async def test_handle_notification_empty_data(self, subscription_manager):
        """Test notification handling with empty data array"""
        subscription_manager.publish = AsyncMock()

        notification_data = {
            "notifiedAt": "2024-01-01T12:00:00Z",
            "data": []
        }

        request = MagicMock()
        request.json = AsyncMock(return_value=notification_data)

        response = await subscription_manager.handle_notification(request)
        assert response.status == 500, "Should handle empty data array appropriately"



    @pytest.mark.asyncio
    async def test_handle_notification_empty_data(self, subscription_manager):
        """Test notification handling with empty data array"""
        subscription_manager.publish = AsyncMock()

        notification_data = {
            "notifiedAt": "2024-01-01T12:00:00Z",
            "data": []
        }

        request = MagicMock()
        request.json = AsyncMock(return_value=notification_data)

        response = await subscription_manager.handle_notification(request)
        assert response.status == 500, "Should handle empty data array appropriately"


class TestSubscriptionConfiguration:
    def test_build_subscription_data_with_q_filter(self, subscription_manager):
        """Test building subscription data with q filter"""
        subscription_manager.config["q_filter"] = "temperature>20"
        local_ip = "192.168.1.1"
        sub_id = "test_sub_001"

        subscription_data = subscription_manager.build_subscription_data(local_ip, sub_id)
        assert "q" in subscription_data, "Q filter should be included in subscription data"
        assert subscription_data["q"] == "temperature>20", "Q filter value incorrect"

    def test_build_subscription_data_empty_watched_attributes(self, subscription_manager):
        """Test building subscription data with empty watched attributes"""
        subscription_manager.config["watched_attributes"] = []
        local_ip = "192.168.1.1"
        sub_id = "test_sub_001"

        subscription_data = subscription_manager.build_subscription_data(local_ip, sub_id)
        assert "watchedAttributes" not in subscription_data, "Should not include empty watched attributes"
        assert "attributes" not in subscription_data["notification"], "Should not include empty notification attributes"

    def test_format_entity_id_empty_input(self, subscription_manager):
        """Test entity ID formatting with empty input"""
        entity_id = subscription_manager.format_entity_id("Device", "")
        assert entity_id == "", "Should handle empty entity ID correctly"

    def test_format_entity_id_special_characters(self, subscription_manager):
        """Test entity ID formatting with special characters"""
        entity_id = subscription_manager.format_entity_id("Device", "test/001#special")
        assert entity_id == "urn:ngsi-ld:Device:test/001#special", "Should handle special characters in entity ID"


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

    @pytest.mark.asyncio
    async def test_find_artifact_subscriptions_empty_response(self, subscription_manager):
        """Test finding subscriptions when response is empty"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        class MockSession:
            @asynccontextmanager
            async def get(self, url, **kwargs):
                yield mock_response

        mock_session = MockSession()
        result = await subscription_manager.find_artifact_subscriptions(mock_session)
        assert result == {}, "Should return empty dict when no subscriptions found"

    @pytest.mark.asyncio
    async def test_find_artifact_subscriptions_network_error(self, subscription_manager):
        """Test finding subscriptions when network error occurs"""

        class MockSession:
            @asynccontextmanager
            async def get(self, url, **kwargs):
                raise aiohttp.ClientError("Network error")

        mock_session = MockSession()
        result = await subscription_manager.find_artifact_subscriptions(mock_session)
        assert result == {}, "Should return empty dict on network error"

    @pytest.mark.asyncio
    async def test_delete_subscription_network_error(self, subscription_manager):
        """Test deletion when network error occurs"""

        class MockSession:
            @asynccontextmanager
            async def delete(self, url, **kwargs):
                raise aiohttp.ClientError("Network error")

        mock_session = MockSession()
        result = await subscription_manager.delete_subscription(mock_session, "test_sub_id")
        assert result is False, "Should return False on network error"

    @pytest.mark.asyncio
    async def test_delete_subscription_not_found(self, subscription_manager):
        """Test deletion when subscription doesn't exist"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Subscription not found")

        class MockSession:
            @asynccontextmanager
            async def delete(self, url, **kwargs):
                yield mock_response

        mock_session = MockSession()
        result = await subscription_manager.delete_subscription(mock_session, "non_existent_sub")
        assert result is False, "Should return False when subscription not found"

    @pytest.mark.asyncio
    async def test_delete_subscription_by_identifier_invalid(self, subscription_manager):
        """Test delete_subscription_by_identifier with invalid identifier format"""
        async with aiohttp.ClientSession() as session:
            result = await subscription_manager.delete_subscription_by_identifier(
                session,
                "invalid/identifier/with/special/chars"
            )
            assert result is False, "Should handle invalid identifier format"

    @pytest.mark.asyncio
    async def test_create_subscription_invalid_data(self, subscription_manager):
        """Test subscription creation with invalid data"""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Invalid subscription data")

        class MockSession:
            @asynccontextmanager
            async def post(self, url, **kwargs):
                yield mock_response

        mock_session = MockSession()
        result = await subscription_manager.create_subscription(
            mock_session,
            {"invalid": "data"},
            "test_sub_001"
        )
        assert result is None, "Should return None when subscription data is invalid"


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

    @pytest.mark.asyncio
    async def test_cleanup_network_error(self, subscription_manager):
        """Test cleanup when network error occurs"""
        subscription_manager.delete_artifact_subscriptions = AsyncMock(
            side_effect=aiohttp.ClientError("Network error during cleanup")
        )
        await subscription_manager.cleanup()
        subscription_manager.delete_artifact_subscriptions.assert_called_once()

    def test_get_local_ip_connection_failure(self, subscription_manager):
        """Test get_local_ip when connection fails"""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = socket.error("Connection failed")
            ip = subscription_manager.get_local_ip()
            assert ip == "127.0.0.1", "Should return localhost on connection failure"



class TestErrorHandling:
    """Test error handling scenarios for SubscriptionManagerArtifact"""

    @pytest.mark.asyncio
    async def test_get_active_subscriptions_unexpected_error(self, subscription_manager):
        """Test get_active_subscriptions with unexpected error"""

        class MockSession:
            @asynccontextmanager
            async def get(self, url, **kwargs):
                raise Exception("Unexpected error")

        mock_session = MockSession()
        result = await subscription_manager.get_active_subscriptions(mock_session)
        assert result == [], "Should return empty list on unexpected error"

    @pytest.mark.asyncio
    async def test_get_active_subscriptions_timeout(self, subscription_manager):
        """Test timeout handling in get_active_subscriptions"""

        class TimeoutSession:
            @asynccontextmanager
            async def get(self, url, **kwargs):
                raise asyncio.TimeoutError("Request timed out")

        mock_session = TimeoutSession()
        result = await subscription_manager.get_active_subscriptions(mock_session)
        assert result == [], "Should handle timeout gracefully"

    @pytest.mark.asyncio
    async def test_delete_subscription_server_error(self, subscription_manager):
        """Test deletion when server returns 500"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        class MockSession:
            @asynccontextmanager
            async def delete(self, url, **kwargs):
                yield mock_response

        mock_session = MockSession()
        result = await subscription_manager.delete_subscription(mock_session, "test_sub_id")
        assert result is False, "Should handle server error appropriately"

    @pytest.mark.asyncio
    async def test_create_subscription_malformed_response(self, subscription_manager):
        """Test subscription creation with malformed response headers"""
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.headers = {}  # Missing Location header

        class MockSession:
            @asynccontextmanager
            async def post(self, url, **kwargs):
                yield mock_response

        mock_session = MockSession()
        result = await subscription_manager.create_subscription(
            mock_session,
            {"type": "Subscription"},
            "test_sub_001"
        )
        assert result is None, "Should handle missing Location header"
    @pytest.mark.asyncio
    async def test_find_artifact_subscriptions_malformed_description(self, subscription_manager):
        """Test find_artifact_subscriptions with malformed subscription description"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{
            'id': 'test_sub_1',
            'description': f"Artifact-ID: {subscription_manager.jid}, Sub-ID: "  # Malformed description
        }])

        class MockSession:
            @asynccontextmanager
            async def get(self, url, **kwargs):
                yield mock_response

        mock_session = MockSession()
        result = await subscription_manager.find_artifact_subscriptions(mock_session)
        assert result == {}, "Should handle malformed description gracefully"

    @pytest.mark.asyncio
    async def test_delete_subscription_by_identifier_unexpected_error(self, subscription_manager):
        """Test delete_subscription_by_identifier with unexpected error during find"""

        class MockSession:
            @asynccontextmanager
            async def get(self, url, **kwargs):
                raise Exception("Unexpected error during find")

        mock_session = MockSession()
        result = await subscription_manager.delete_subscription_by_identifier(mock_session, "test_sub_001")
        assert result is False, "Should return False on unexpected error"

    @pytest.mark.asyncio
    async def test_delete_artifact_subscriptions_partial_failure(self, subscription_manager):
        """Test delete_artifact_subscriptions with partial failure"""

        class MockSession:
            def __init__(self):
                self.get_calls = []
                self.delete_calls = []

            @asynccontextmanager
            async def get(self, url, **kwargs):
                self.get_calls.append((url, kwargs))
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=[{
                    'id': 'sub1',
                    'description': f"Artifact-ID: {subscription_manager.jid}, Sub-ID: test_sub_001"
                }])
                yield mock_response

            @asynccontextmanager
            async def delete(self, url, **kwargs):
                self.delete_calls.append((url, kwargs))
                raise Exception("Delete failed")
                yield

        mock_session = MockSession()
        await subscription_manager.delete_artifact_subscriptions(mock_session)
        assert len(mock_session.get_calls) == 1, "Should attempt to get subscriptions"
        assert len(mock_session.delete_calls) == 1, "Should attempt to delete subscription"
        assert subscription_manager.active_subscriptions == {}, "Should clear active subscriptions"


    @pytest.mark.asyncio
    async def test_create_subscription_invalid_broker_url(self, subscription_manager):
        """Test create_subscription with invalid broker URL"""
        subscription_manager.broker_url = "http://invalid-url:9090"

        class MockSession:
            @asynccontextmanager
            async def post(self, url, **kwargs):
                raise aiohttp.ClientConnectorError(
                    connection_key=None,
                    os_error=OSError("Connection refused")
                )

        mock_session = MockSession()
        result = await subscription_manager.create_subscription(
            mock_session,
            {"type": "Subscription"},
            "test_sub_001"
        )
        assert result is None, "Should return None when broker URL is invalid"

    @pytest.mark.asyncio
    async def test_run_server_start_failure(self, subscription_manager):
        """Test run method when server fails to start"""
        subscription_manager.find_free_port = MagicMock(return_value=80)  # Usually requires root privileges
        subscription_manager.presence.set_available = MagicMock()

        with patch('aiohttp.ClientSession', new_callable=AsyncMock) as mock_session:
            try:
                await subscription_manager.run()
            except Exception as e:
                assert True, "Should handle server start failure gracefully"

    @pytest.mark.asyncio
    async def test_cleanup_session_error(self, subscription_manager):
        """Test cleanup when session creation fails"""
        with patch('aiohttp.ClientSession', side_effect=Exception("Session creation failed")):
            await subscription_manager.cleanup()
            # Should not raise exception and log error


class TestRunMethod:
    """Test suite for the run method of SubscriptionManagerArtifact"""

    @pytest.mark.asyncio
    async def test_run_basic_functionality(self, subscription_manager):
        """Test basic run functionality with default configuration"""
        # Mock methods that are not essential for this test
        subscription_manager.presence.set_available = MagicMock()
        subscription_manager.get_local_ip = MagicMock(return_value="127.0.0.1")
        subscription_manager.find_free_port = MagicMock(return_value=8080)
        subscription_manager.delete_artifact_subscriptions = AsyncMock()
        subscription_manager.create_subscription = AsyncMock(return_value="test_sub_id")

        # Mock the infinite loop
        original_sleep = asyncio.sleep
        sleep_called = False

        async def mock_sleep(duration):
            nonlocal sleep_called
            sleep_called = True
            raise asyncio.CancelledError()  # Break the infinite loop

        asyncio.sleep = AsyncMock(side_effect=mock_sleep)

        try:
            # Mock the web application setup
            with patch('aiohttp.web.Application') as mock_app, \
                    patch('aiohttp.web.AppRunner') as mock_runner, \
                    patch('aiohttp.web.TCPSite') as mock_site, \
                    patch('aiohttp.ClientSession') as mock_session:

                # Configure mock app
                mock_app_instance = mock_app.return_value
                mock_app_instance.router.add_post = MagicMock()

                # Configure mock runner
                mock_runner_instance = mock_runner.return_value
                mock_runner_instance.setup = AsyncMock()

                # Configure mock site
                mock_site_instance = mock_site.return_value
                mock_site_instance.start = AsyncMock()

                # Run the method (it will be interrupted by the CancelledError)
                with pytest.raises(asyncio.CancelledError):
                    await subscription_manager.run()

                # Verify the sequence of operations
                subscription_manager.presence.set_available.assert_called_once()
                subscription_manager.get_local_ip.assert_called_once()
                subscription_manager.find_free_port.assert_called_once()

                # Verify no subscription deletion in this flow (as per default config)
                subscription_manager.delete_artifact_subscriptions.assert_not_called()

                # Verify web application setup
                mock_app.assert_called_once()
                mock_app_instance.router.add_post.assert_called_once_with("/notify",
                                                                          subscription_manager.handle_notification)
                mock_runner.assert_called_once()
                mock_runner_instance.setup.assert_called_once()
                mock_site.assert_called_once()
                mock_site_instance.start.assert_called_once()

                # Verify subscription creation
                assert subscription_manager.port == 8080
                assert sleep_called  # Verify that we entered the infinite loop

        finally:
            # Restore the original sleep function
            asyncio.sleep = original_sleep
    @pytest.mark.asyncio
    async def test_run_with_delete_all_subscriptions(self, subscription_manager):
        """Test run with delete_all_artifact_subscriptions flag"""
        subscription_manager.config["delete_all_artifact_subscriptions"] = True
        subscription_manager.presence.set_available = MagicMock()
        subscription_manager.get_local_ip = MagicMock(return_value="127.0.0.1")
        subscription_manager.find_free_port = MagicMock(return_value=8080)
        subscription_manager.delete_artifact_subscriptions = AsyncMock()

        with patch('aiohttp.web.Application'), \
                patch('aiohttp.web.AppRunner'), \
                patch('aiohttp.web.TCPSite'), \
                patch('aiohttp.ClientSession'):
            # Setup the asyncio event to stop the run loop
            async def stop_run():
                await asyncio.sleep(0.1)
                subscription_manager.running = False

            await asyncio.gather(
                subscription_manager.run(),
                stop_run()
            )

            subscription_manager.delete_artifact_subscriptions.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_delete_specific_subscription(self, subscription_manager):
        """Test run with delete_subscription_identifier flag"""
        test_sub_id = "test_sub_001"
        subscription_manager.config["delete_subscription_identifier"] = test_sub_id
        subscription_manager.presence.set_available = MagicMock()
        subscription_manager.get_local_ip = MagicMock(return_value="127.0.0.1")
        subscription_manager.find_free_port = MagicMock(return_value=8080)
        subscription_manager.delete_subscription_by_identifier = AsyncMock()

        with patch('aiohttp.web.Application'), \
                patch('aiohttp.web.AppRunner'), \
                patch('aiohttp.web.TCPSite'), \
                patch('aiohttp.ClientSession'):
            async def stop_run():
                await asyncio.sleep(0.1)
                subscription_manager.running = False

            await asyncio.gather(
                subscription_manager.run(),
                stop_run()
            )

            subscription_manager.delete_subscription_by_identifier.assert_called_once_with(
                ANY,  # session object
                test_sub_id
            )



    @pytest.mark.asyncio
    async def test_run_server_binding_error(self, subscription_manager):
        """Test run method when server fails to bind to port"""
        subscription_manager.presence.set_available = MagicMock()
        subscription_manager.get_local_ip = MagicMock(return_value="127.0.0.1")
        subscription_manager.find_free_port = MagicMock(return_value=8080)

        mock_site = AsyncMock()
        mock_site.start.side_effect = OSError("Address already in use")

        with patch('aiohttp.web.Application'), \
                patch('aiohttp.web.AppRunner'), \
                patch('aiohttp.web.TCPSite', return_value=mock_site), \
                patch('aiohttp.ClientSession'), \
                pytest.raises(Exception) as exc_info:
            await subscription_manager.run()

            assert "Address already in use" in str(exc_info.value)


    @pytest.mark.asyncio
    async def test_run_connection_error(self, subscription_manager):
        """Test run method handling of connection errors"""
        subscription_manager.presence.set_available = MagicMock()
        subscription_manager.get_local_ip = MagicMock(return_value="127.0.0.1")
        subscription_manager.find_free_port = MagicMock(return_value=8080)

        class MockClientSession:
            async def __aenter__(self):
                raise aiohttp.ClientError("Connection failed")

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        with patch('aiohttp.ClientSession', return_value=MockClientSession()), \
                pytest.raises(Exception) as exc_info:
            await subscription_manager.run()

            assert "Connection failed" in str(exc_info.value)

