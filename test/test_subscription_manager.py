import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from spade_fiware_artifacts.context_broker_suscription_manager import SubscriptionManagerArtifact
import aiohttp
from unittest import IsolatedAsyncioTestCase

class TestSubscriptionManagerArtifact(IsolatedAsyncioTestCase):
    def setUp(self):
        self.jid = 'test@localhost'
        self.passwd = 'password'
        self.broker_url = 'http://testbroker.com'
        self.artifact = SubscriptionManagerArtifact(self.jid, self.passwd, self.broker_url)
        self.artifact.presence = MagicMock()

    async def test_setup(self):
        await self.artifact.setup()
        self.artifact.presence.set_available.assert_called_once()

    async def test_setup_exception(self):
        self.artifact.presence.set_available.side_effect = Exception('Test Exception')
        with patch('loguru.logger.error') as mock_logger_error:
            await self.artifact.setup()
            self.artifact.presence.set_available.assert_called_once()
            mock_logger_error.assert_called_once()
            args, kwargs = mock_logger_error.call_args
            self.assertIn('Failed to set presence', args[0])

    def test_get_local_ip(self):
        ip = self.artifact.get_local_ip()
        self.assertIsInstance(ip, str)

    def test_get_local_ip_exception(self):
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.connect.side_effect = Exception('Test Exception')
            ip = self.artifact.get_local_ip()
            self.assertEqual(ip, '127.0.0.1')

    def test_format_entity_id(self):
        entity_type = 'TestType'
        entity_id = '12345'
        formatted_id = self.artifact.format_entity_id(entity_type, entity_id)
        self.assertEqual(formatted_id, 'urn:ngsi-ld:TestType:12345')

        entity_id = 'urn:ngsi-ld:TestType:12345'
        formatted_id = self.artifact.format_entity_id(entity_type, entity_id)
        self.assertEqual(formatted_id, entity_id)

        entity_id = ''
        formatted_id = self.artifact.format_entity_id(entity_type, entity_id)
        self.assertEqual(formatted_id, '')

    def test_format_entity_id_none(self):
        entity_type = 'TestType'
        entity_id = None
        formatted_id = self.artifact.format_entity_id(entity_type, entity_id)
        self.assertEqual(formatted_id, None)

    async def test_create_subscription_success(self):
        subscription_data = {"type": "Subscription"}

        # Create a mock response object
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.headers.get.return_value = 'subscription-id'
        mock_response.text = AsyncMock(return_value='Error')

        # Mock the __aenter__ and __aexit__ methods as AsyncMock
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__ = AsyncMock(return_value=None)  # Properly mock __aexit__

        # Mock the session.post method to return an object for 'async with'
        session = AsyncMock()
        session.post = AsyncMock(return_value=mock_response)

        result = await self.artifact.create_subscription(session, subscription_data)
        self.assertEqual('subscription-id', result)
        session.post.assert_awaited_once()

    async def test_create_subscription_failure(self):
        subscription_data = {"type": "Subscription"}
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='Error')
        mock_response.__aenter__.return_value = mock_response
        session = AsyncMock()
        session.post.return_value = mock_response

        result = await self.artifact.create_subscription(session, subscription_data)
        self.assertIsNone(result)
        session.post.assert_called_once()

    async def test_create_subscription_unexpected_exception(self):
        subscription_data = {"type": "Subscription"}
        session = AsyncMock()
        session.post.side_effect = Exception('Test Exception')
        with patch('loguru.logger.error') as mock_logger_error:
            result = await self.artifact.create_subscription(session, subscription_data)
            self.assertIsNone(result)
            session.post.assert_called_once()
            mock_logger_error.assert_called_once()
            args, kwargs = mock_logger_error.call_args
            self.assertIn('Unexpected error occurred', args[0])

    async def test_get_active_subscriptions_success(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{'id': 'sub1', 'entities': [], 'watchedAttributes': []}])
        mock_response.__aenter__.return_value = mock_response
        session = AsyncMock()
        session.get.return_value = mock_response

        subscriptions = await self.artifact.get_active_subscriptions(session)
        self.assertEqual(len(subscriptions), 0)
        session.get.assert_called_once()

    async def test_get_active_subscriptions_failure(self):
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='Error')
        mock_response.__aenter__.return_value = mock_response
        session = AsyncMock()
        session.get.return_value = mock_response

        subscriptions = await self.artifact.get_active_subscriptions(session)
        self.assertEqual(subscriptions, [])
        session.get.assert_called_once()

    async def test_get_active_subscriptions_client_error(self):
        session = AsyncMock()
        session.get.side_effect = aiohttp.ClientError('Test Client Error')
        with patch('loguru.logger.error') as mock_logger_error:
            subscriptions = await self.artifact.get_active_subscriptions(session)
            self.assertEqual(subscriptions, [])
            session.get.assert_called_once()


    async def test_delete_subscription_success(self):
        subscription_id = 'sub1'
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__.return_value = mock_response
        session = AsyncMock()
        session.delete.return_value = mock_response

        result = await self.artifact.delete_subscription(session, subscription_id)
        session.delete.assert_called_once()

    async def test_delete_subscription_failure(self):
        subscription_id = 'sub1'
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='Error')
        mock_response.__aenter__.return_value = mock_response
        session = AsyncMock()
        session.delete.return_value = mock_response

        result = await self.artifact.delete_subscription(session, subscription_id)
        self.assertFalse(result)
        session.delete.assert_called_once()

    async def test_delete_subscription_client_error(self):
        subscription_id = 'sub1'
        session = AsyncMock()
        session.delete.side_effect = aiohttp.ClientError('Test Client Error')
        with patch('loguru.logger.error') as mock_logger_error:
            result = await self.artifact.delete_subscription(session, subscription_id)
            self.assertFalse(result)
            session.delete.assert_called_once()
            mock_logger_error.assert_called_once()

    async def test_handle_notification_success(self):
        notification_data = {
            'data': [{'id': 'entity1', 'type': 'TestType', 'attr1': 'value1'}],
            'notifiedAt': '2023-10-01T00:00:00Z'
        }
        request = AsyncMock()
        request.json = AsyncMock(return_value=notification_data)
        self.artifact.watched_attributes = ['attr1']

        with patch.object(self.artifact, 'publish', new=AsyncMock()) as mock_publish:
            response = await self.artifact.handle_notification(request)
            self.assertEqual(response.status, 200)
            self.assertIn('Notification received and processed', await response.text())
            self.assertIn('entity1', self.artifact.recent_notifications)
            self.assertEqual(self.artifact.recent_notifications['entity1']['notifiedAt'], '2023-10-01T00:00:00Z')
            mock_publish.assert_awaited_once()

    async def test_handle_notification_invalid_json(self):
        request = AsyncMock()
        request.json = AsyncMock(side_effect=json.JSONDecodeError('Expecting value', '', 0))

        response = await self.artifact.handle_notification(request)
        self.assertEqual(response.status, 400)
        self.assertIn('Invalid JSON', await response.text())

    async def test_handle_notification_exception(self):
        request = AsyncMock()
        request.json = AsyncMock(side_effect=Exception('Test Exception'))

        response = await self.artifact.handle_notification(request)
        self.assertEqual(response.status, 500)
        self.assertIn('Internal Server Error', await response.text())

    async def test_handle_notification_missing_data(self):
        notification_data = {}
        request = AsyncMock()
        request.json = AsyncMock(return_value=notification_data)
        with patch('loguru.logger.error') as mock_logger_error:
            response = await self.artifact.handle_notification(request)
            self.assertEqual(response.status, 500)
            self.assertIn('Internal Server Error', await response.text())
            mock_logger_error.assert_called_once()
            args, kwargs = mock_logger_error.call_args
            self.assertIn('Unexpected error while handling notification', args[0])

    async def test_handle_notification_missing_id(self):
        notification_data = {
            'data': [{'type': 'TestType', 'attr1': 'value1'}],  # 'id' missing
            'notifiedAt': '2023-10-01T00:00:00Z'
        }
        request = AsyncMock()
        request.json = AsyncMock(return_value=notification_data)
        with patch.object(self.artifact, 'publish', new=AsyncMock()) as mock_publish:
            response = await self.artifact.handle_notification(request)
            self.assertEqual(response.status, 200)
            self.assertIn('Notification received and processed', await response.text())
            # Since 'id' is missing, recent_notifications should not be updated
            self.assertNotIn(None, self.artifact.recent_notifications)
            mock_publish.assert_awaited_once()

    async def test_handle_notification_missing_notifiedAt(self):
        notification_data = {
            'data': [{'id': 'entity1', 'type': 'TestType', 'attr1': 'value1'}],
            # 'notifiedAt' missing
        }
        request = AsyncMock()
        request.json = AsyncMock(return_value=notification_data)
        with patch.object(self.artifact, 'publish', new=AsyncMock()) as mock_publish:
            response = await self.artifact.handle_notification(request)
            self.assertEqual(response.status, 200)
            self.assertIn('Notification received and processed', await response.text())
            # Since 'notifiedAt' is missing, recent_notifications should not be updated
            self.assertNotIn('entity1', self.artifact.recent_notifications)
            mock_publish.assert_awaited_once()

    async def test_handle_notification_all_attributes(self):
        notification_data = {
            'data': [{'id': 'entity1', 'type': 'TestType', 'attr1': 'value1', 'attr2': 'value2'}],
            'notifiedAt': '2023-10-01T00:00:00Z'
        }
        request = AsyncMock()
        request.json = AsyncMock(return_value=notification_data)
        self.artifact.watched_attributes = []  # Empty, so include all attributes

        with patch.object(self.artifact, 'publish', new=AsyncMock()) as mock_publish:
            response = await self.artifact.handle_notification(request)
            self.assertEqual(response.status, 200)
            self.assertIn('Notification received and processed', await response.text())
            # Check that all attributes are included
            mock_publish.assert_awaited_once()
            publish_arg = mock_publish.call_args[0][0]
            self.assertIn('attr1', publish_arg)
            self.assertIn('attr2', publish_arg)

    async def test_handle_notification_filtered_attributes(self):
        notification_data = {
            'data': [{'id': 'entity1', 'type': 'TestType', 'attr1': 'value1', 'attr2': 'value2'}],
            'notifiedAt': '2023-10-01T00:00:00Z'
        }
        request = AsyncMock()
        request.json = AsyncMock(return_value=notification_data)
        self.artifact.watched_attributes = ['attr1']

        with patch.object(self.artifact, 'publish', new=AsyncMock()) as mock_publish:
            response = await self.artifact.handle_notification(request)
            self.assertEqual(response.status, 200)
            self.assertIn('Notification received and processed', await response.text())
            # Check that only 'attr1' is included
            mock_publish.assert_awaited_once()
            publish_arg = mock_publish.call_args[0][0]
            data_published = json.loads(publish_arg)
            entity_data = data_published['data'][0]
            self.assertIn('attr1', entity_data)
            self.assertNotIn('attr2', entity_data)

    async def test_review_and_delete_subscriptions_no_subscriptions(self):
        session = AsyncMock()
        self.artifact.get_active_subscriptions = AsyncMock(return_value=[])
        with patch('builtins.input', return_value='q'):
            await self.artifact.review_and_delete_subscriptions(session)
            self.artifact.get_active_subscriptions.assert_awaited_once()

    async def test_review_and_delete_subscriptions_delete(self):
        session = AsyncMock()
        subscriptions = [{'id': 'sub1'}, {'id': 'sub2'}]
        self.artifact.get_active_subscriptions = AsyncMock(return_value=subscriptions)
        self.artifact.delete_subscription = AsyncMock(return_value=True)
        with patch('builtins.input', side_effect=['1', 'q']):
            await self.artifact.review_and_delete_subscriptions(session)
            self.artifact.get_active_subscriptions.assert_awaited_once()
            self.artifact.delete_subscription.assert_awaited_once_with(session, 'sub1')

    async def test_review_and_delete_subscriptions_invalid_input(self):
        session = AsyncMock()
        subscriptions = [{'id': 'sub1'}, {'id': 'sub2'}]
        self.artifact.get_active_subscriptions = AsyncMock(return_value=subscriptions)
        self.artifact.delete_subscription = AsyncMock()
        with patch('builtins.input', side_effect=['invalid', 'q']), patch('loguru.logger.warning') as mock_logger_warning:
            await self.artifact.review_and_delete_subscriptions(session)
            self.artifact.get_active_subscriptions.assert_awaited_once()
            self.artifact.delete_subscription.assert_not_called()
            mock_logger_warning.assert_called_with("Invalid input. Please enter a number or 'q'.")

    async def test_run_exception(self):
        self.artifact.presence.set_available = MagicMock()
        self.artifact.get_local_ip = MagicMock(return_value='127.0.0.1')
        self.artifact.review_and_delete_subscriptions = AsyncMock()
        with patch('builtins.input', side_effect=Exception('Test Exception')), patch('loguru.logger.error') as mock_logger_error:
            await self.artifact.run()
            mock_logger_error.assert_called()
            args, kwargs = mock_logger_error.call_args
            self.assertIn('An error occurred while running the artifact', args[0])
