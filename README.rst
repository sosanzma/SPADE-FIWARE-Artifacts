SPADE-FIWARE-Artifacts
=======================

Documentation
-------------
Check out the  documentation at: https://spade-fiware-artifacts.readthedocs.io

.. image:: https://readthedocs.org/projects/spade-fiware-artifacts/badge/?version=latest
    :target: https://spade-fiware-artifacts.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/actions/workflow/status/sosanzma/spade-fiware-artifacts/python-app.yml
    :target: https://github.com/sosanzma/spade-fiware-artifacts/actions
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/sosanzma/SPADE-FIWARE-Artifacts/badge.svg
    :target: https://coveralls.io/github/sosanzma/SPADE-FIWARE-Artifacts

.. image:: https://img.shields.io/pypi/v/spade-fiware-artifacts
    :target: https://pypi.org/project/spade-fiware-artifacts/
    :alt: PyPI Version

Overview
--------

SPADE-FIWARE-Artifacts is a Python library that bridges SPADE (Smart Python Agent Development Environment) with FIWARE Context Brokers. It provides a toolkit for multi-agent systems to interact with FIWARE's context management system, supporting both Orion and Scorpio Context Brokers through NGSI-LD.

Key Features
------------

- **NGSI-LD Support**: Full compatibility with FIWARE's NGSI-LD API
- **Asynchronous Operations**: Built on asyncio for efficient non-blocking operations
- **Flexible Data Processing**: Customizable data transformation and handling
- **Configurable JSON Templates**: Allows customized JSON templates for data structuring and flexible formatting.

Core Components
---------------

InserterArtifact
~~~~~~~~~~~~~~~~

A component for managing entity data in FIWARE Context Brokers:

- **Entity Management**:
  - Create new entities with complex attributes
  - Update existing entities (full or partial updates)
  - Handle different attribute types (Properties, GeoProperties, Relationships)

Example usage::

    inserter = InserterArtifact(
        jid="inserter@xmpp.server",
        passwd="password",
        publisher_jid="publisher@xmpp.server",
        host="broker.example.com",
        project_name="my_project"
    )

SubscriptionManagerArtifact
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manages subscriptions and handles notifications from the Context Broker:

- **Subscription Features**:
  - Create and manage NGSI-LD subscriptions
  - Monitor specific entity attributes under specific conditions
  - Handle subscription lifecycle (create, update, delete)

Example usage::

    subscription_manager = SubscriptionManagerArtifact(
        jid="subscriber@xmpp.server",
        passwd="password",
        config=config_payload,
        broker_url="http://broker.example.com:9090"
    )

where::

    config_payload = {
        "entity_type": "WasteContainer",
        "entity_id": "088",
        "watched_attributes": [],
        "q_filter": "fillingLevel>0.7",
        "context": [
            "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"
        ],
        "delete_all_artefact_subscriptions": true,
        "delete_subscription_identifier": "subs_1",
        "subscription_identifier": "subs_2",
        "delete_only": false
    }

Installation
------------

Install via pip::

    pip install spade-fiware-artifacts

Quick Start
-----------

1. **Configure Your Environment**

   Create a `config.json` file::

       {
           "XMPP_SERVER": "your.xmpp.server",
           "subscriber_artifact_name": "art_subscriber",
           "broker_port": "http://localhost:9090"
       }

2. **Initialize Artifacts**

   .. code-block:: python

       from spade_fiware_artifacts import InserterArtifact, SubscriptionManagerArtifact

       inserter = InserterArtifact(
           jid="inserter@xmpp.server",
           passwd="password",
           publisher_jid="publisher@xmpp.server",
           host="localhost",
           project_name="test_project"
       )
