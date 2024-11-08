Use Case Guide :  `insterter_context_broker`
===============================================

Introduction
------------

This guide provides a comprehensive explanation on how to use the SPADE-FIWARE artifacts and connect to a FIWARE Context Broker. We'll focus on the example file ``inserter_context_broker.py`` and the associated JSON files to illustrate the process.

Example Structure
-----------------

The example consists of the following files:

1. ``inserter_context_broker.py``: The main script demonstrating the use of the artifacts.
2. ``config.json``: Configuration file for system parameters.
3. ``json_template.json``: Template for the NGSI-LD entity structure.
4. ``payload.json``: Example data to be inserted into the Context Broker.

Detailed Code Explanation
-------------------------

inserter_context_broker.py
^^^^^^^^^^^^^^^^^^^^^^^^^^

This file contains two main classes and a ``main`` function:

PublisherArtifact
"""""""""""""""""

.. code-block:: python

    class PublisherArtifact(spade_artifact.Artifact):
        def __init__(self, jid, passwd, payload):
            super().__init__(jid, passwd)
            self.payload = payload

        async def setup(self):
            self.presence.set_available()
            await asyncio.sleep(2)

        async def run(self):
            while True:
                if self.presence.is_available():
                    payload_json = json.dumps(self.payload)
                    logger.info(f"Publishing data: {payload_json}")
                    await self.publish(str(payload_json))
                await asyncio.sleep(360)

This artifact simulates a data source. In a real scenario, it could be replaced by any external data source (API, database, IoT device, etc.).

- ``__init__``: Initializes the artifact with a JID (Jabber ID), password, and payload.
- ``setup``: Sets the artifact's presence as available.
- ``run``: Periodically publishes the payload as a JSON string.

main Function
"""""""""""""

.. code-block:: python

    async def main():
        # Load configurations
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)

        # PublisherArtifact configuration
        XMPP_SERVER = config["XMPP_SERVER"]
        publisher_name = config["publisher_artifact_name"]
        publisher_jid = f"{publisher_name}@{XMPP_SERVER}"
        publisher_passwd = getpass.getpass(prompt="Password for publisher artifact> ")

        with open('payload.json', 'r') as payload_file:
            payload = json.load(payload_file)

        with open('json_template.json', 'r') as json_template_file:
            json_template = json.load(json_template_file)

        publisher = PublisherArtifact(publisher_jid, publisher_passwd, payload)

        # InserterArtifact configuration
        subscriber_name = config["subscriber_artifact_name"]
        subscriber_jid = f"{subscriber_name}@{XMPP_SERVER}"
        subscriber_passwd = getpass.getpass(prompt="Password for subscriber artifact> ")

        host = config["host"]
        project_name = config["project_name"]

        subscriber = InserterArtifact(subscriber_jid, subscriber_passwd, publisher_jid, host,
                                      project_name, json_template=json_template)

        # Start artifacts
        await publisher.start()
        await subscriber.start()

        # Wait for artifacts to finish
        await asyncio.gather(publisher.join(), subscriber.join())

        # Stop artifacts
        await publisher.stop()
        await subscriber.stop()

        print("Agents and Artifacts have been stopped")

The ``main`` function sets up and runs both the ``PublisherArtifact`` and ``InserterArtifact``. It loads configurations from JSON files, initializes the artifacts, and manages their lifecycle.

Configuration Files
-------------------

config.json
^^^^^^^^^^^

.. code-block:: json

    {
        "XMPP_SERVER": "sosanzma.lan",
        "publisher_artifact_name": "publisher_artifact",
        "subscriber_artifact_name": "subscriber_artifact",
        "host": "localhost",
        "project_name": "ngb"
    }

This file contains the general configuration for the system:

- ``XMPP_SERVER``: The XMPP server address.
- ``publisher_artifact_name``: The name for the publisher artifact.
- ``subscriber_artifact_name``: The name for the subscriber (inserter) artifact.
- ``host``: The Context Broker host address.
- ``project_name``: The project name used as a tenant in the Context Broker.

json_template.json
^^^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "id": "urn:ngsi-ld:{type}:{id}",
        "type": "{type}",
        "location": {
            "type": "Point",
            "coordinates": "{coordinates}"
        },
        "address": {
            "type": "Property",
            "value": {
                "addressCountry": {
                    "type": "string",
                    "value": "{country}"
                },
                "addressLocality": {
                    "type": "string",
                    "value": "{locality}"
                },
                "streetAddress": {
                    "type": "string",
                    "value": "{street_address}"
                },
                "streetNr": {
                    "type": "string",
                    "value": "{street_number}"
                }
            }
        },
        "status": {
            "type": "Property",
            "value": "{status}"
        },
        "storedWasteKind": {
            "type": "Property",
            "value": "{waste_kind}"
        },
        "fillingLevel": {
            "type": "Property",
            "value":"{filling_level}"
        },
        "Provider": {
            "type": "Property",
            "value":"{provider}"
        },
        "@context": "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"
    }

This file defines the template for the NGSI-LD entity structure. The placeholders in curly braces (e.g., ``{type}``, ``{id}``) will be replaced with actual values from the payload.

payload.json
^^^^^^^^^^^^

.. code-block:: json

    {
        "type": "WasteContainer",
        "id": "003",
        "coordinates": [20.4168, -20.7038],
        "country": "Spain",
        "locality": "Madrid",
        "street_address": "Calle Colón",
        "street_number": "56",
        "status": "no-active",
        "waste_kind" : "Organic",
        "provider" : "Manel"
    }

This file contains example data that will be inserted into the Context Broker. In a real-world scenario, this data would come from your actual data source.
How to Use
----------

1. **Setup**: Ensure you have all required dependencies installed and the FIWARE Context Broker is running.

2. **Configuration**:
   - Modify ``config.json`` to match your XMPP server and Context Broker settings.
   - Adjust ``json_template.json`` if you need a different entity structure.
   - Update ``payload.json`` with your actual data or replace it with your data source.

3. **Run the Script**: Execute ``inserter_context_broker.py``. You'll be prompted to enter passwords for the publisher and subscriber artifacts.

4. **Monitor**: The script will start publishing data and inserting it into the Context Broker. Monitor the console output for any errors or successful insertions.

.. warning::
   The example is configured to use port 9090 by default, as the ``InserterArtifact`` class is parameterized for this port. If you want to use the Orion Context Broker, which typically runs on port 1026, you should modify the port in your configuration or when initializing the ``InserterArtifact``.

   It's important to note that the default port 9090 is typically used for testing or development environments. For production use with the Orion Context Broker, you must change this to port 1026.

   To change the port:


   Update the ``InserterArtifact`` initialization in ``inserter_context_broker.py``:

      .. code-block:: python

         subscriber = InserterArtifact(subscriber_jid, subscriber_passwd, publisher_jid, f"{host}:1026",
                                       project_name, json_template=json_template)

   Make sure to use the correct port (1026 for Orion Context Broker) to ensure proper communication with your FIWARE environment.
Customization
-------------

- **Data Source**: Replace the ``PublisherArtifact`` with your own data source implementation. Ensure it provides data in a format compatible with your ``json_template.json``.

- **Data Processing**: Implement a custom data processor in the ``InserterArtifact`` to transform your data if needed.

- **Entity Structure**: Modify ``json_template.json`` to match your desired entity structure in the Context Broker.

- **Update Frequency**: Adjust the sleep time in the ``PublisherArtifact.run()`` method to change how often data is published.

Troubleshooting
---------------

- Ensure all JSON files are correctly formatted.
- Check that the XMPP server and Context Broker are running and accessible.
- Verify that the provided JIDs and passwords are correct.
- If entities are not being created/updated, check the Context Broker logs for any errors.

Conclusion
----------

This example demonstrates how to use SPADE-FIWARE-Artifacts to publish data to a FIWARE Context Broker. By understanding and customizing this example, you can adapt it to your specific use case, whether it's integrating with different data sources, modifying the entity structure, or adjusting the data processing logic.