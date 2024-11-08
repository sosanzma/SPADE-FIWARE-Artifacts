Use Case Guide: `InserterArtifact`
=================================

Introduction
-----------

The ``InserterArtifact`` class is a  component of the SPADE-FIWARE-Artifacts toolkit that facilitates the insertion and updating of data in FIWARE Context Brokers. It provides a robust interface for managing entities in NGSI-LD format, supporting both creation and updates of entities with various attribute types.

Key Features
-----------

1. **Asynchronous Operation**
   - Built on ``asyncio`` for non-blocking operations

2. **Flexible Entity Management**
   - Automatic entity existence checking
   - Creation of new entities when needed
   - Support for partial updates of specific attributes

3. **NGSI-LD Support**
   - Full compatibility with NGSI-LD format
   - Handles Properties, GeoProperties, and Relationships
   - Customizable JSON templates for entity structure

4. **Data Processing**
   - Customizable data processor function
   - Built-in JSON cleaning and validation
   - Template-based payload construction

Class Structure
--------------

Constructor Parameters
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def __init__(self, jid, passwd, publisher_jid, host, project_name, columns_update=[],
                 data_processor=None, json_template=None, json_exceptions=None, port='9090'):

- ``jid``: Jabber ID for the artifact
- ``passwd``: Password for authentication
- ``publisher_jid``: JID of the publisher artifact
- ``host``: Context Broker host address
- ``project_name``: Project identifier
- ``columns_update``: List of specific columns to update (optional)
- ``data_processor``: Custom data processing function (optional)
- ``json_template``: Template for JSON payload construction (optional)
- ``json_exceptions``: Exceptions for JSON cleaning rules (optional)
- ``port``: Context Broker port (default: '9090')

Core Methods
^^^^^^^^^^^

Entity Management
"""""""""""""""

.. code-block:: python

    async def process_and_send_data(self, payload: dict)
    async def update_specific_attributes(self, entity_id: str, entity_data: dict)
    async def update_or_create_entity(self, entity_id: str, entity_data: dict, payload: dict)
    async def entity_exists(self, entity_id: str) -> bool
    async def create_new_entity(self, entity_data: dict)
    async def update_entity_attribute(self, entity_id: str, attribute: str, attribute_data: dict, context: any)
    async def update_all_attributes(self, entity_id, entity_data, context)

JSON Handling
"""""""""""

.. code-block:: python

    def build_entity_json(self, payload, clean=True)

Integration Flow
--------------

The ``run()`` Method
^^^^^^^^^^^^^^^^^^

The ``run()`` method is the core of the ``InserterArtifact``, orchestrating the entire data flow:

1. Sets the artifact's presence to available
2. Enters an infinite loop to:
   - Wait for data from the payload queue
   - Process incoming data
   - Send data to the Context Broker
3. Handles errors and maintains continuous operation

Data Flow Process
^^^^^^^^^^^^^^^

1. **Data Reception**:
   - Receives data through the ``artifact_callback`` method
   - Processes data using the configured ``data_processor``
   - Adds processed data to the payload queue

2. **Data Processing**:
   - Retrieves data from the queue
   - Constructs entity ID and JSON structure
   - Validates and cleans the data

3. **Entity Management**:
   - Checks if entity exists
   - Updates or creates entities as needed
   - Handles specific attribute updates

Use Cases and Examples
--------------------

1. IoT Device Integration
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Example: IoT sensor data integration
    json_template = {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "id": "urn:ngsi-ld:Sensor:{device_id}",
        "type": "Sensor",
        "temperature": {
            "type": "Property",
            "value": "{temperature}"
        },
        "humidity": {
            "type": "Property",
            "value": "{humidity}"
        },
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": ["{longitude}", "{latitude}"]
            }
        }
    }

    inserter = InserterArtifact(
        jid="sensor_inserter@xmpp.server",
        passwd="password",
        publisher_jid="sensor_publisher@xmpp.server",
        host="context.broker.host",
        project_name="iot_project",
        json_template=json_template
    )

2. Real-time Monitoring System
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Example: System monitoring with specific attribute updates
    def process_monitoring_data(data):
        return [{
            "id": data["system_id"],
            "type": "MonitoringSystem",
            "cpu_usage": data["cpu"],
            "memory_usage": data["memory"],
            "disk_usage": data["disk"]
        }]

    inserter = InserterArtifact(
        jid="monitor_inserter@xmpp.server",
        passwd="password",
        publisher_jid="monitor_publisher@xmpp.server",
        host="context.broker.host",
        project_name="monitoring",
        columns_update=["cpu_usage", "memory_usage", "disk_usage"],
        data_processor=process_monitoring_data
    )

3. Smart City Application
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Example: Traffic monitoring system
    json_template = {
        "@context": "https://smart-data-models.github.io/dataModel.Transportation/context.jsonld",
        "id": "urn:ngsi-ld:TrafficFlowObserved:{intersection_id}",
        "type": "TrafficFlowObserved",
        "vehicleCount": {
            "type": "Property",
            "value": "{count}"
        },
        "averageSpeed": {
            "type": "Property",
            "value": "{speed}"
        },
        "congestionLevel": {
            "type": "Property",
            "value": "{congestion}"
        }
    }

Advanced Features
---------------

Custom Data Processing
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def custom_processor(data):
        # Transform incoming data
        processed_data = []
        for item in data["items"]:
            processed_item = {
                "id": item["id"],
                "type": "CustomEntity",
                # Add more transformations
            }
            processed_data.append(processed_item)
        return processed_data

    inserter = InserterArtifact(
        # ... other parameters ...
        data_processor=custom_processor
    )

Selective Attribute Updates
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    inserter = InserterArtifact(
        # ... other parameters ...
        columns_update=["temperature", "humidity"],  # Only update these attributes
    )

Best Practices
------------

1. **Error Handling**
   - Implement proper error handling in data processor functions
   - Monitor the artifact's logs for potential issues
   - Handle network connectivity issues gracefully

2. **Performance Optimization**
   - Use batch processing when possible
   - Implement efficient data processing functions
   - Monitor queue size and processing delays

3. **Data Validation**
   - Validate data before processing
   - Use appropriate JSON templates
   - Handle missing or invalid data appropriately

Troubleshooting
-------------

Common Issues
^^^^^^^^^^^

1. **Connection Errors**
   - Verify Context Broker URL and port
   - Check network connectivity
   - Ensure proper authentication

2. **Data Processing Issues**
   - Validate JSON template format
   - Check data processor function
   - Verify incoming data structure

3. **Update Failures**
   - Confirm entity existence
   - Verify attribute names and types
   - Check NGSI-LD compatibility

Conclusion
---------

The ``InserterArtifact`` provides a flexible solution for managing data in FIWARE Context Brokers. Its versatility makes it suitable for various use cases, from IoT applications to smart city implementations.