import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
import json
import pytest
from spade_fiware_artifacts.context_broker_inserter import InserterArtifact

class TestInserterArtifact(unittest.TestCase):
    def setUp(self):
        self.jid = 'test@localhost'
        self.passwd = 'password'
        self.publisher_jid = 'publisher@localhost'
        self.host = 'testbroker.com'
        self.project_name = 'TestProject'
        self.columns_update = ['attribute1', 'attribute2']
        self.port = '9090'
        self.artifact = InserterArtifact(
            self.jid,
            self.passwd,
            self.publisher_jid,
            self.host,
            self.project_name,
            self.columns_update,
            json_template={
                "id": "urn:ngsi-ld:TestEntity:{id}",
                "type": "{type}",
                "attribute1": {"type": "Property", "value": "{value1}"},
                "attribute2": {"type": "Property", "value": "{value2}"},
                "@context": ["https://example.com/context.jsonld"]
            }
        )
        self.artifact.presence = MagicMock()
        self.artifact.link = AsyncMock()
        self.artifact.payload_queue = asyncio.Queue()

    @pytest.mark.asyncio
    async def test_setup(self):
        with patch('asyncio.sleep', return_value=None):
            await self.artifact.setup()
            self.artifact.presence.set_available.assert_called_once()
            self.artifact.link.assert_called_once_with(self.publisher_jid, self.artifact.artifact_callback)

    def test_default_data_processor(self):
        data = {'key': 'value'}
        result = self.artifact.default_data_processor(data)
        self.assertEqual(result, [data])

    def test_artifact_callback(self):
        payload = json.dumps({'id': '123', 'type': 'TestType', 'value1': 'val1', 'value2': 'val2'})
        data_processor_mock = MagicMock(return_value=[{'processed_data': True}])
        self.artifact.data_processor = data_processor_mock

        with patch('asyncio.create_task') as mock_create_task:
            self.artifact.artifact_callback('artifact', payload)
            data_processor_mock.assert_called_once()
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_and_send_data(self):
        payload = {'id': '123', 'type': 'TestType', 'value1': 'val1', 'value2': 'val2'}
        self.artifact.columns_update = ['attribute1']
        with patch.object(self.artifact, 'update_specific_attributes') as mock_update_specific_attributes:
            await self.artifact.process_and_send_data(payload)
            mock_update_specific_attributes.assert_called_once()

    def test_build_entity_json(self):
        payload = {'id': '123', 'type': 'TestType', 'value1': 'val1', 'value2': 'val2'}
        result = self.artifact.build_entity_json(payload)
        expected_result = {
            'id': 'urn:ngsi-ld:TestEntity:123',
            'type': 'TestType',
            'attribute1': {'type': 'Property', 'value': 'val1'},
            'attribute2': {'type': 'Property', 'value': 'val2'},
            '@context': ['https://example.com/context.jsonld']
        }
        self.assertEqual(result, expected_result)

    @pytest.mark.asyncio
    async def test_entity_exists_true(self):
        entity_id = 'urn:ngsi-ld:TestEntity:123'
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await self.artifact.entity_exists(entity_id)
            self.assertTrue(result)

    @pytest.mark.asyncio
    async def test_entity_exists_false(self):
        entity_id = 'urn:ngsi-ld:TestEntity:123'
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await self.artifact.entity_exists(entity_id)
            self.assertFalse(result)

    @pytest.mark.asyncio
    async def test_create_new_entity_success(self):
        entity_data = {'id': 'urn:ngsi-ld:TestEntity:123', 'type': 'TestType'}
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.text = AsyncMock(return_value='Created')
            mock_response.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_response

            await self.artifact.create_new_entity(entity_data)
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_new_entity_failure(self):
        entity_data = {'id': 'urn:ngsi-ld:TestEntity:123', 'type': 'TestType'}
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value='Error')
            mock_response.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_response

            await self.artifact.create_new_entity(entity_data)
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_entity_attribute_success(self):
        entity_id = 'urn:ngsi-ld:TestEntity:123'
        attribute = 'attribute1'
        attribute_data = {'value': 'new_value'}
        context = ['https://example.com/context.jsonld']
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response_patch = AsyncMock()
            mock_response_patch.status = 204
            mock_response_patch.__aenter__.return_value = mock_response_patch
            mock_session.return_value.__aenter__.return_value.patch.return_value = mock_response_patch

            await self.artifact.update_entity_attribute(entity_id, attribute, attribute_data, context)
            mock_session.return_value.__aenter__.return_value.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_entity_attribute_failure(self):
        entity_id = 'urn:ngsi-ld:TestEntity:123'
        attribute = 'attribute1'
        attribute_data = {'value': 'new_value'}
        context = ['https://example.com/context.jsonld']
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response_patch = AsyncMock()
            mock_response_patch.status = 404
            mock_response_patch.text = AsyncMock(return_value='Not Found')
            mock_response_patch.__aenter__.return_value = mock_response_patch
            mock_session.return_value.__aenter__.return_value.patch.return_value = mock_response_patch

            mock_response_post = AsyncMock()
            mock_response_post.status = 204
            mock_response_post.__aenter__.return_value = mock_response_post
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_response_post

            await self.artifact.update_entity_attribute(entity_id, attribute, attribute_data, context)
            mock_session.return_value.__aenter__.return_value.patch.assert_called_once()
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_run(self):
        self.artifact.presence.set_available = MagicMock()
        payload = {'id': '123', 'type': 'TestType', 'value1': 'val1', 'value2': 'val2'}
        self.artifact.payload_queue.put_nowait(payload)
        with patch.object(self.artifact, 'process_and_send_data') as mock_process_and_send_data:
            with patch('asyncio.sleep', side_effect=asyncio.CancelledError):
                with self.assertRaises(asyncio.CancelledError):
                    await self.artifact.run()
                mock_process_and_send_data.assert_called_once_with(payload)
