SPADE-FIWARE-Artifacts
=======================

.. image:: https://readthedocs.org/projects/spade-fiware-artifacts/badge/?version=latest
    :target: https://spade-fiware-artifacts.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

SPADE-FIWARE-Artifacts is a powerful toolkit that bridges the gap between SPADE (Smart Python Agent Development Environment) and FIWARE, specifically focusing on interaction with the Orion and Scorpio Context Brokers. This project provides a set of artifacts that enable SPADE-based multi-agent systems to seamlessly interact with FIWARE's context management capabilities.

Features
--------

InserterArtifact
^^^^^^^^^^^^^^^^

The core of this toolkit is the ``InserterArtifact`` class, which facilitates sophisticated communication with FIWARE Context Brokers. Key features include:

1. **Flexible Data Processing**: 
   
   - Customizable data processor function allows for tailored data transformation before insertion.
   - The data processor must output a JSON format that respects the expected payload structure.
   - Default processor provided, but can be easily overridden for specific use cases.
   - This flexibility allows integration with various data sources, including APIs, databases, and more.

2. **Entity Management**:
   
   - **Intelligent Entity Handling**: The artifact checks if an entity exists before deciding to create or update.
   - **Create New Entities**: If an entity doesn't exist, it's created with all provided attributes.
   - **Update Existing Entities**: For existing entities, the artifact can:
     
     - Update specific attributes
     - Update all attributes
   - **Attribute Addition**: If an update includes a new attribute not present in the existing entity, it's automatically added.

3. **NGSI-LD Support**: 
   
   - Full support for NGSI-LD format, ensuring compatibility with modern FIWARE deployments.
   - Handles different types of attributes: Properties, GeoProperties, and Relationships.

4. **Asynchronous Operations**: 
   
   - Utilizes ``asyncio`` for non-blocking operations, allowing efficient handling of multiple requests.

5. **Configurable JSON Templates**: 
   
   - Uses customizable JSON templates for structuring data, providing flexibility in entity representation.

6. **Robust Error Handling and Logging**: 
   
   - Comprehensive error handling and detailed logging using the ``loguru`` library.

PublisherArtifact
^^^^^^^^^^^^^^^^^

The ``PublisherArtifact`` class provided in the example is a simple demonstration of how data can be fed into the system. However, it's important to note:

- This is just a basic example and not limited to the functionality shown.
- In real-world scenarios, this could be replaced or extended to integrate with any external data source.
- The true power of the system lies in its ability to work with diverse data sources, such as APIs, databases, IoT devices, or any other data stream.

How It Works
------------

1. **Configuration**: 
   
   - The system uses separate configuration files (``config.json``, ``json_template.json``, ``payload.json``) for easy customization.

2. **Data Flow**:
   
   - Data is ingested from an external source (API, database, IoT devices, etc.)
   - The data processor transforms this data into the required JSON format, matching the expected payload structure.
   - ``InserterArtifact`` receives this processed JSON data and sends it to the FIWARE Context Broker.

3. **Entity Handling Process**:
   
   - The artifact checks if the entity exists in the Context Broker.
   - If it exists:
     
     - Updates are applied to the existing entity.
     - New attributes are added if they don't already exist.
   - If it doesn't exist:
     
     - A new entity is created with all provided attributes.

4. **XMPP Communication**: 
   
   - Utilizes SPADE's artifact system for communication between data source and inserter.

Installation
------------

.. code-block:: bash

   pip install spade_fiware_artifacts

Quick Start
-----------

Using InserterArtifact
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from spade_fiware_artifacts import InserterArtifact

   inserter = InserterArtifact(
       jid="inserter@example.com",
       password="password",
       publisher_jid="data_source@example.com",
       host="contextbroker.example.com",
       project_name="my_project"
   )

   await inserter.start()

Configuration
^^^^^^^^^^^^^

Customize the behavior by modifying:

- ``config.json``: General configuration settings
- ``json_template.json``: Template for entity structure
- ``payload.json``: Example of data structure (in real scenarios, this would come from your data source)

Advanced Usage
--------------

Custom Data Processor
^^^^^^^^^^^^^^^^^^^^^

The data processor is where the magic happens. You can define a custom data processor to transform data from your specific source into the JSON format expected by the Context Broker:

.. code-block:: python

   def custom_processor(data):
       # Your custom logic here
       # This could involve complex transformations, data cleaning, etc.
       # The output MUST be a JSON that matches the expected payload structure
       processed_data = {
           "id": data["some_id"],
           "type": "YourEntityType",
           "attribute1": {
               "type": "Property",
               "value": data["some_value"]
           },
           # ... other attributes ...
       }
       return processed_data

   inserter = InserterArtifact(
       # ... other parameters ...
       data_processor=custom_processor
   )

Specific Attribute Updates
^^^^^^^^^^^^^^^^^^^^^^^^^^

To update only specific attributes:

.. code-block:: python

   inserter = InserterArtifact(
       # ... other parameters ...
       columns_update=['attribute1', 'attribute2']
   )

Integrating with Different Data Sources
---------------------------------------

The toolkit's flexibility allows for integration with various data sources. Here are a few examples:

1. **API Integration**:

   .. code-block:: python

      import requests
      import json

      def api_data_processor(data):
          response = requests.get('https://api.example.com/data')
          api_data = response.json()
          # Transform api_data to match expected payload format
          transformed_data = {
              "id": f"urn:ngsi-ld:YourEntity:{api_data['id']}",
              "type": "YourEntityType",
              "attribute1": {
                  "type": "Property",
                  "value": api_data["some_value"]
              },
              # ... other attributes ...
          }
          return json.dumps(transformed_data)  # Ensure output is JSON string

      inserter = InserterArtifact(data_processor=api_data_processor, ...)

2. **Database Integration**:

   .. code-block:: python

      import sqlite3
      import json

      def db_data_processor(data):
          conn = sqlite3.connect('your_database.db')
          cursor = conn.cursor()
          cursor.execute('SELECT * FROM your_table')
          db_data = cursor.fetchall()
          # Transform db_data to match expected payload format
          transformed_data = {
              "id": f"urn:ngsi-ld:YourEntity:{db_data[0][0]}",
              "type": "YourEntityType",
              "attribute1": {
                  "type": "Property",
                  "value": db_data[0][1]
              },
              # ... other attributes ...
          }
          return json.dumps(transformed_data)  # Ensure output is JSON string

      inserter = InserterArtifact(data_processor=db_data_processor, ...)

3. **IoT Device Integration**:

   .. code-block:: python

      import paho.mqtt.client as mqtt
      import json

      def on_message(client, userdata, message):
          # This function will be called when a message is received
          payload = message.payload.decode()
          # Process the payload and transform it to match expected format
          transformed_data = {
              "id": f"urn:ngsi-ld:IoTDevice:{payload['device_id']}",
              "type": "IoTDevice",
              "temperature": {
                  "type": "Property",
                  "value": payload["temp"]
              },
              # ... other attributes ...
          }
          return json.dumps(transformed_data)  # Ensure output is JSON string

      def iot_data_processor(data):
          client = mqtt.Client()
          client.on_message = on_message
          client.connect("mqtt.example.com", 1883)
          client.loop_start()
          # ... logic to subscribe to topics, etc.

      inserter = InserterArtifact(data_processor=iot_data_processor, ...)

These examples demonstrate how to process data from different sources and ensure that the output is a JSON string that matches the expected payload format. Remember to always use ``json.dumps()`` to convert your processed data into a JSON string before returning it from your data processor.

Compatibility
-------------

These artifacts are compatible with both Orion and Scorpio Context Brokers, allowing you to work with either implementation of the NGSI-LD API.

Documentation
-------------

For detailed documentation, please visit our `ReadTheDocs documentation <https://spade-fiware-artifacts.readthedocs.io/en/latest/>`_.

Contributing
------------

Contributions are welcome! Please feel free to submit a Pull Request.

License
-------

This project is licensed under the MIT License.