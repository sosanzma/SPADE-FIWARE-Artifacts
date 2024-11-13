import aiohttp
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientError, ClientConnectionError
from yarl import URL


from spade_fiware_artifacts.context_broker_inserter import InserterArtifact
from aioresponses import aioresponses


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


class TestInserterSetup:
    """Tests related to InserterArtifact setup functionality"""

    @pytest.mark.asyncio
    async def test_setup_presence_failure(self, inserter):
        """Test setup when presence.set_available() fails"""
        inserter.presence.set_available.side_effect = Exception("Presence error")
        inserter.link = AsyncMock()

        await inserter.setup()
        # Should continue despite presence error
        inserter.link.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_with_sleep(self, inserter):
        """Test setup with sleep timing"""
        inserter.link = AsyncMock()

        with patch('asyncio.sleep') as mock_sleep:
            await inserter.setup()
            mock_sleep.assert_called_once_with(1)


class TestPayloadProcessing:
    """Tests related to payload processing functionality"""

    @pytest.mark.asyncio
    async def test_process_payload_with_missing_type(self, inserter):
        """Test processing payload with missing type field"""
        invalid_payload = {
            "id": "test1",
            "temperature": {"value": 25.0}
        }
        await inserter.process_and_send_data(invalid_payload)
        # Should log error and return without making requests

    @pytest.mark.asyncio
    async def test_process_payload_with_custom_processor(self, inserter):
        """Test processing payload with custom data processor"""

        def custom_processor(data):
            data['processed'] = True
            return [data]

        inserter.data_processor = custom_processor
        test_payload = '{"type": "TestEntity", "id": "test1"}'

        inserter.artifact_callback("test_artifact", test_payload)
        await asyncio.sleep(0)

        queue_item = await inserter.payload_queue.get()
        assert queue_item['processed'] is True


class TestEntityOperations:
    """Tests related to entity CRUD operations"""

    @pytest.mark.asyncio
    async def test_entity_exists_connection_error(self, inserter):
        """Test entity existence check with connection error"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            url = f"{inserter.api_url}/{entity_id}"

            mocked.get(url, exception=ClientConnectionError())

            result = await inserter.entity_exists(entity_id)
            assert result is False

    @pytest.mark.asyncio
    async def test_update_entity_attribute_geo_property(self, inserter):
        """Test updating a GeoProperty attribute"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            attribute = "location"
            attribute_data = {
                "coordinates": [40.123, -3.456]
            }
            context = inserter.json_template["@context"]

            patch_url = f"{inserter.api_url}/{entity_id}/attrs/{attribute}"
            mocked.patch(patch_url, status=204)

            await inserter.update_entity_attribute(entity_id, attribute, attribute_data, context)

    @pytest.mark.asyncio
    async def test_update_entity_attribute_relationship(self, inserter):
        """Test updating a Relationship attribute"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            attribute = "relatedTo"
            attribute_data = {
                "object": "urn:ngsi-ld:RelatedEntity:obj1"
            }
            context = inserter.json_template["@context"]

            patch_url = f"{inserter.api_url}/{entity_id}/attrs/{attribute}"
            mocked.patch(patch_url, status=204)

            await inserter.update_entity_attribute(entity_id, attribute, attribute_data, context)

    @pytest.mark.asyncio
    async def test_update_entity_attribute_not_found(self, inserter):
        """Test updating a non-existent attribute"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            attribute = "temperature"
            attribute_data = {"value": 25.0}
            context = inserter.json_template["@context"]

            patch_url = f"{inserter.api_url}/{entity_id}/attrs/{attribute}"
            post_url = f"{inserter.api_url}/{entity_id}/attrs"

            # Mock PATCH failure due to non-existent attribute
            mocked.patch(patch_url, status=207)
            # Mock successful POST to create attribute
            mocked.post(post_url, status=204)

            await inserter.update_entity_attribute(entity_id, attribute, attribute_data, context)

    @pytest.mark.asyncio
    async def test_update_all_attributes_mixed_types(self, inserter):
        """Test updating multiple attributes of different types"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            entity_data = {
                "temperature": {"value": 25.0},
                "location": {"coordinates": [40.123, -3.456]},
                "relatedTo": {"object": "urn:ngsi-ld:RelatedEntity:obj1"},
                "@context": inserter.json_template["@context"]
            }

            # Mock responses for each attribute
            for attr in ["temperature", "location", "relatedTo"]:
                patch_url = f"{inserter.api_url}/{entity_id}/attrs/{attr}"
                mocked.patch(patch_url, status=204)

            await inserter.update_all_attributes(
                entity_id,
                entity_data,
                entity_data["@context"]
            )


class TestJsonTemplateHandling:
    """Tests related to JSON template processing"""

    def test_build_entity_json_with_missing_context(self, inserter):
        """Test building entity JSON when context is missing from template"""
        inserter.json_template = {}  # Remove context from template
        payload = {
            "type": "TestEntity",
            "id": "test1",
            "temperature": {"value": 25.0}
        }

        result = inserter.build_entity_json(payload)
        # Should log error about missing context

    def test_build_entity_json_with_placeholders(self, inserter):
        """Test building entity JSON with placeholder substitution"""
        inserter.json_template = {
            "id": "urn:ngsi-ld:TestEntity:{id}",
            "type": "{type}",
            "temperature": {"value": "{temperature}"},
            "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        }

        payload = {
            "id": "test1",
            "type": "TestEntity",
            "temperature": 25.0
        }

        result = inserter.build_entity_json(payload)
        assert result["id"] == "urn:ngsi-ld:TestEntity:test1"
        assert result["type"] == "TestEntity"
        assert result["temperature"]["value"] == 25.0

    def test_build_entity_json_with_exceptions(self, inserter):
        """Test building entity JSON with custom exceptions"""
        inserter.json_exceptions = {
            "custom_field": "custom_value"
        }
        inserter.json_template = {
            "custom_field": {"type": "Property"},
            "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        }

        payload = {}
        result = inserter.build_entity_json(payload, clean=False)
        assert "custom_field" in result
        assert result["custom_field"]["value"] == "None"


class TestRunMethod:
    """Tests related to the run method functionality"""

    @pytest.mark.asyncio
    async def test_run_method_exception_handling(self, inserter):
        """Test run method's exception handling"""

        inserter.process_and_send_data = AsyncMock(side_effect=Exception("Processing error"))

        await inserter.payload_queue.put({"type": "TestEntity", "id": "test1"})

        task = asyncio.create_task(inserter.run())

        await asyncio.sleep(0.2)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        inserter.presence.set_available.assert_called_once()


class TestErrorHandling:
    """Tests focusing on error handling scenarios"""

    @pytest.mark.asyncio
    async def test_artifact_callback_invalid_json(self, inserter):
        """Test handling of invalid JSON in artifact_callback"""
        invalid_payload = "{'invalid': json"
        inserter.artifact_callback("test_artifact", invalid_payload)
        await asyncio.sleep(0)  # Allow async queue operations to complete
        assert inserter.payload_queue.empty()  # Invalid JSON should not be queued

    @pytest.mark.asyncio
    async def test_build_entity_json_missing_context(self, inserter):
        """Test build_entity_json when context is missing"""
        inserter.json_template = {"field": "value"}  # Template without @context
        payload = {"type": "TestEntity", "id": "test1"}
        result = inserter.build_entity_json(payload)
        assert "@context" not in result

    @pytest.mark.asyncio
    async def test_create_new_entity_failure(self, inserter):
        with aioresponses() as mocked:
            # Try adding payload format and headers
            mocked.post(
                inserter.api_url,
                status=400,
                payload={"error": "Invalid entity data"},
                headers={'Content-Type': 'application/json'}
            )

            entity_data = {
                "id": "urn:ngsi-ld:TestEntity:test1",
                "type": "TestEntity",
                "@context": inserter.json_template["@context"]
            }

            await inserter.create_new_entity(entity_data)

            # Alternative way to check requests
            request_list = mocked.requests[('POST', URL(inserter.api_url))]
            assert len(request_list) == 1

    @pytest.mark.asyncio
    async def test_update_entity_attribute_patch_failure(self, inserter):
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            attribute = "temperature"
            attribute_data = {"value": 25.0}
            context = inserter.json_template["@context"]

            patch_url = f"{inserter.api_url}/{entity_id}/attrs/{attribute}"

            # Try adding more specific mock
            mocked.patch(
                patch_url,
                status=500,
                payload={"error": "Internal server error"},
                headers={'Content-Type': 'application/json'}
            )

            await inserter.update_entity_attribute(
                entity_id, attribute, attribute_data, context)

            # Alternative way to check requests
            request_list = mocked.requests[('PATCH', URL(patch_url))]
            assert len(request_list) == 1

    @pytest.mark.asyncio
    async def test_update_entity_attribute_post_failure(self, inserter):
        """Test update_entity_attribute with POST failure after PATCH"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            attribute = "temperature"
            attribute_data = {"value": 25.0}
            context = inserter.json_template["@context"]

            patch_url = f"{inserter.api_url}/{entity_id}/attrs/{attribute}"
            post_url = f"{inserter.api_url}/{entity_id}/attrs"

            # Mock PATCH indicating attribute doesn't exist
            mocked.patch(
                URL(patch_url),
                status=207
            )

            # Mock failed POST
            mocked.post(
                URL(post_url),
                status=500,
                payload={"error": "Internal server error"},
                headers={'Content-Type': 'application/json'}
            )

            await inserter.update_entity_attribute(
                entity_id, attribute, attribute_data, context
            )

            # Verify both requests were made
            assert len(mocked.requests[("PATCH", URL(patch_url))]) == 1
            assert len(mocked.requests[("POST", URL(post_url))]) == 1

    @pytest.mark.asyncio
    async def test_update_all_attributes_failure(self, inserter):
        """Test update_all_attributes with mixed success/failure responses"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            entity_data = {
                "temperature": {"value": 25.0},
                "humidity": {"value": 60},
                "@context": inserter.json_template["@context"]
            }

            # Mock successful temperature update
            temp_url = f"{inserter.api_url}/{entity_id}/attrs/temperature"
            mocked.patch(
                URL(temp_url),
                status=204
            )

            # Mock failed humidity update
            humid_url = f"{inserter.api_url}/{entity_id}/attrs/humidity"
            mocked.patch(
                URL(humid_url),
                status=500,
                payload={"error": "Internal server error"},
                headers={'Content-Type': 'application/json'}
            )

            await inserter.update_all_attributes(
                entity_id, entity_data, entity_data["@context"]
            )

            # Verify both attributes were attempted
            assert len(mocked.requests[("PATCH", URL(temp_url))]) == 1
            assert len(mocked.requests[("PATCH", URL(humid_url))]) == 1

    @pytest.mark.asyncio
    async def test_entity_exists_network_error(self, inserter):
        """Test entity_exists with network connection error"""
        with aioresponses() as mocked:
            entity_id = "urn:ngsi-ld:TestEntity:test1"
            url = f"{inserter.api_url}/{entity_id}"

            # Mock network error
            mocked.get(url, exception=aiohttp.ClientConnectionError(
                "Connection refused"))

            exists = await inserter.entity_exists(entity_id)
            assert exists is False  # Should return False on connection error