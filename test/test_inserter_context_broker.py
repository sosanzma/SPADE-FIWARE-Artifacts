import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientResponse, ClientError
from spade_fiware_artifacts.context_broker_inserter import InserterArtifact


@pytest.fixture
def inserter():
    """Basic InserterArtifact fixture with minimal mocking"""
    with patch('spade_fiware_artifacts.context_broker_inserter.spade_artifact.Artifact'):
        artifact = InserterArtifact(
            jid="test@example.com",
            passwd="password",
            publisher_jid="publisher@example.com",
            host="localhost",
            project_name="test"
        )
        artifact.presence = MagicMock()
        artifact.json_template = {
            "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        }
        return artifact


@pytest.mark.asyncio
async def test_setup_success(inserter):
    """Test successful setup with minimal mocking"""
    inserter.link = AsyncMock()
    await inserter.setup()

    inserter.presence.set_available.assert_called_once()
    inserter.link.assert_called_once_with(
        inserter.publisher_jid,
        inserter.artifact_callback
    )


@pytest.mark.asyncio
async def test_setup_link_failure(inserter):
    """Test setup failure when link fails"""
    inserter.link = AsyncMock(side_effect=Exception("Link failed"))

    with pytest.raises(Exception, match="Link failed"):
        await inserter.setup()

    inserter.presence.set_available.assert_called_once()


@pytest.mark.asyncio
async def test_process_valid_payload(inserter):
    """Test processing a valid payload"""
    test_payload = {
        "type": "TestEntity",
        "id": "test1",
        "temperature": {"value": 25.0}
    }

    # Mock only the necessary methods
    inserter.update_or_create_entity = AsyncMock()
    await inserter.process_and_send_data(test_payload)

    inserter.update_or_create_entity.assert_called_once()
    call_args = inserter.update_or_create_entity.call_args[0]
    assert "urn:ngsi-ld:TestEntity:test1" in call_args


@pytest.mark.asyncio
async def test_process_invalid_payload(inserter):
    """Test processing an invalid payload (missing required fields)"""
    invalid_payload = {
        "temperature": {"value": 25.0}  # Missing type and id
    }

    inserter.update_or_create_entity = AsyncMock()
    await inserter.process_and_send_data(invalid_payload)

    inserter.update_or_create_entity.assert_not_called()
"""
class TestEntityInserter:
    @pytest.mark.asyncio
    async def test_entity_exists_success(self, inserter):

    @pytest.mark.asyncio
    async def test_entity_exists_not_found(self, inserter):


    @pytest.mark.asyncio
    async def test_create_new_entity_success(self, inserter):

    @pytest.mark.asyncio
    async def test_create_new_entity_failure(self, inserter):


"""


@pytest.mark.asyncio
async def test_update_specific_attributes(inserter):
    """Test updating specific attributes"""
    inserter.columns_update = ["temperature"]
    inserter.update_entity_attribute = AsyncMock()

    entity_data = {
        "temperature": {"value": 25.0},
        "@context": inserter.json_template["@context"]
    }

    await inserter.update_specific_attributes(
        "urn:ngsi-ld:TestEntity:test1",
        entity_data
    )

    inserter.update_entity_attribute.assert_called_once_with(
        "urn:ngsi-ld:TestEntity:test1",
        "temperature",
        {"value": 25.0},
        inserter.json_template["@context"]
    )


@pytest.mark.asyncio
async def test_artifact_callback_valid_json(inserter):
    """Test artifact callback with valid JSON payload"""
    test_payload = '{"type": "TestEntity", "id": "test1", "temperature": {"value": 25.0}}'
    inserter.data_processor = MagicMock(return_value=[{"processed": "data"}])
    inserter.payload_queue.put = AsyncMock()

    inserter.artifact_callback("test_artifact", test_payload)
    await asyncio.sleep(0)  # Allow async task to complete

    inserter.payload_queue.put.assert_called_once_with({"processed": "data"})


@pytest.mark.asyncio
async def test_artifact_callback_invalid_json(inserter):
    """Test artifact callback with invalid JSON payload"""
    invalid_payload = 'invalid json'
    inserter.data_processor = MagicMock()
    inserter.payload_queue.put = AsyncMock()

    inserter.artifact_callback("test_artifact", invalid_payload)
    await asyncio.sleep(0)

    inserter.data_processor.assert_not_called()
    inserter.payload_queue.put.assert_not_called()