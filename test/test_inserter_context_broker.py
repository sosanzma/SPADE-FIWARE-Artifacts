import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError, ClientSession
from spade_fiware_artifacts.context_broker_inserter import InserterArtifact


class MockClientSession:
    def __init__(self):
        self.get = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.fixture
def mock_aiohttp_client_session():
    return MockClientSession()
@pytest.fixture
def mock_artifact():
    with patch('spade_fiware_artifacts.context_broker_inserter.spade_artifact.Artifact', autospec=True) as mock:
        mock_instance = mock.return_value
        mock_instance.presence = MagicMock()
        yield mock_instance

@pytest.fixture
def inserter_artifact():
    with patch('spade_fiware_artifacts.context_broker_inserter.spade_artifact.Artifact', autospec=True):
        inserter = InserterArtifact(
            jid="test@example.com",
            passwd="password",
            publisher_jid="publisher@example.com",
            host="localhost",
            project_name="test_project"
        )
        inserter.presence = MagicMock()
        inserter.link = AsyncMock()
        # Proporcionar un contexto de prueba
        inserter.json_template = {
            "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        }
        return inserter

@pytest.mark.asyncio
async def test_setup(inserter_artifact):
    await inserter_artifact.setup()
    inserter_artifact.presence.set_available.assert_called_once()
    inserter_artifact.link.assert_called_once_with(inserter_artifact.publisher_jid, inserter_artifact.artifact_callback)


@pytest.mark.asyncio
async def test_setup_link_failure(inserter_artifact):
    with patch.object(inserter_artifact, 'link', new_callable=AsyncMock) as mock_link:
        mock_link.side_effect = Exception("Link failed")
        with pytest.raises(Exception, match="Link failed"):
            await inserter_artifact.setup()


@pytest.mark.asyncio
async def test_artifact_callback(inserter_artifact):
    test_payload = '{"type": "TestEntity", "id": "test1"}'
    with patch.object(inserter_artifact, 'data_processor') as mock_processor:
        mock_processor.return_value = [{"processed": "data"}]
        with patch.object(inserter_artifact.payload_queue, 'put', new_callable=AsyncMock) as mock_put:
            inserter_artifact.artifact_callback("test_artifact", test_payload)
            await asyncio.sleep(0)  # Allow the async task to complete
            mock_put.assert_called_once_with({"processed": "data"})


@pytest.mark.asyncio
async def test_artifact_callback_invalid_json(inserter_artifact):
    invalid_payload = 'invalid json'
    with patch.object(inserter_artifact, 'data_processor') as mock_processor:
        inserter_artifact.artifact_callback("test_artifact", invalid_payload)
        mock_processor.assert_not_called()


@pytest.mark.asyncio
async def test_process_and_send_data_update_specific_attributes(inserter_artifact):
    inserter_artifact.columns_update = ['attribute1']
    payload = {"type": "TestEntity", "id": "test1", "attribute1": {"value": "test"}}
    with patch.object(inserter_artifact, 'update_specific_attributes', new_callable=AsyncMock) as mock_update:
        await inserter_artifact.process_and_send_data(payload)
        mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_process_and_send_data_update_or_create_entity(inserter_artifact):
    payload = {"type": "TestEntity", "id": "test1", "attribute1": {"value": "test"}}
    with patch.object(inserter_artifact, 'update_or_create_entity', new_callable=AsyncMock) as mock_update_or_create:
        await inserter_artifact.process_and_send_data(payload)
        mock_update_or_create.assert_called_once()


@pytest.mark.asyncio
async def test_update_specific_attributes(inserter_artifact):
    entity_id = "urn:ngsi-ld:TestEntity:test1"
    entity_data = {"attribute1": {"value": "test"}, "@context": "test_context"}
    inserter_artifact.columns_update = ['attribute1']
    with patch.object(inserter_artifact, 'update_entity_attribute', new_callable=AsyncMock) as mock_update:
        await inserter_artifact.update_specific_attributes(entity_id, entity_data)
        mock_update.assert_called_once_with(entity_id, 'attribute1', {"value": "test"}, "test_context")


@pytest.mark.asyncio
async def test_update_or_create_entity_existing(inserter_artifact):
    entity_id = "urn:ngsi-ld:TestEntity:test1"
    entity_data = {"attribute1": {"value": "test"}, "@context": "test_context"}
    payload = {"type": "TestEntity", "id": "test1", "attribute1": {"value": "test"}}
    with patch.object(inserter_artifact, 'entity_exists', new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = True
        with patch.object(inserter_artifact, 'update_all_attributes', new_callable=AsyncMock) as mock_update:
            await inserter_artifact.update_or_create_entity(entity_id, entity_data, payload)
            mock_update.assert_called_once_with(entity_id, entity_data, "test_context")


@pytest.mark.asyncio
async def test_update_or_create_entity_new(inserter_artifact):
    entity_id = "urn:ngsi-ld:TestEntity:test1"
    entity_data = {"attribute1": {"value": "test"}, "@context": "test_context"}
    payload = {"type": "TestEntity", "id": "test1", "attribute1": {"value": "test"}}
    with patch.object(inserter_artifact, 'entity_exists', new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = False
        with patch.object(inserter_artifact, 'create_new_entity', new_callable=AsyncMock) as mock_create:
            await inserter_artifact.update_or_create_entity(entity_id, entity_data, payload)
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_entity_exists(inserter_artifact, mock_aiohttp_client_session):
    entity_id = "urn:ngsi-ld:TestEntity:test1"
    mock_aiohttp_client_session.get.return_value.__aenter__.return_value.status = 200

    with patch('aiohttp.ClientSession', return_value=mock_aiohttp_client_session):
        result = await inserter_artifact.entity_exists(entity_id)
        assert result is True
        mock_aiohttp_client_session.get.assert_called_once_with(
            f"{inserter_artifact.api_url}/{entity_id}",
            headers=inserter_artifact.headers
        )


@pytest.mark.asyncio
async def test_entity_not_exists(inserter_artifact, mock_aiohttp_client_session):
    entity_id = "urn:ngsi-ld:TestEntity:test1"
    mock_aiohttp_client_session.get.return_value.__aenter__.return_value.status = 404

    with patch('aiohttp.ClientSession', return_value=mock_aiohttp_client_session):
        result = await inserter_artifact.entity_exists(entity_id)
        assert result is False