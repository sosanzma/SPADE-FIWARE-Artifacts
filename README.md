# SPADE-FIWARE-Artifacts

SPADE-FIWARE-Artifacts is a toolkit that bridges the gap between SPADE (Smart Python Agent Development Environment) and FIWARE, specifically the Orion and Scorpio Context Brokers. This project provides a set of artifacts that enable SPADE-based multi-agent systems to seamlessly interact with FIWARE's context management capabilities.

## Features

- **InserterArtifact**: Facilitates the insertion and updating of data in the Context Broker.
- **SubscriberArtifact**: Manages subscriptions to entity changes in the Context Broker.
- Asynchronous communication with FIWARE components.
- Flexible data processing and transformation.
- Support for NGSI-LD entity creation, updates, and subscriptions.
- Compatible with both Orion and Scorpio Context Brokers.

## Installation

```bash
pip install spade-fiware-artifacts
```

## Quick Start

### Using InserterArtifact

```python
from spade_fiware_artifacts import InserterArtifact

inserter = InserterArtifact(
    jid="inserter@example.com",
    password="password",
    publisher_jid="publisher@example.com",
    host="contextbroker.example.com",
    project_name="my_project"
)

await inserter.start()
```

### Using SubscriberArtifact

```python
from spade_fiware_artifacts import SubscriberArtifact

subscriptions = [
    {
        "entity_id": "urn:ngsi-ld:WasteContainer:001",
        "entity_type": "WasteContainer",
        "attributes": ["fillingLevel", "temperature"],
        "conditions": {"fillingLevel": 0.8}
    },
    {
        "entity_type": "WasteContainer",
        "attributes": ["modelName", "tankMaterial"]
    }
]

subscriber = SubscriberArtifact(
    jid="subscriber@example.com",
    passwd="password",
    scorpio_ip="contextbroker.example.com",
    project_name="my_project",
    subscriptions=subscriptions
)

await subscriber.start()
```

## Detailed Usage

### InserterArtifact

The InserterArtifact allows you to:

- Create new entities in the Context Broker
- Update existing entities
- Handle different types of attributes (Properties, GeoProperties, Relationships)
- Process and transform data before insertion

### SubscriberArtifact

The SubscriberArtifact enables you to:

- Create subscriptions for specific entities or entity types
- Filter subscriptions by attributes
- Set conditions for notifications
- Receive and process notifications from the Context Broker

Both artifacts are designed to work with NGSI-LD, the latest evolution of FIWARE's context information management API.

## Configuration

Both artifacts require configuration parameters such as XMPP credentials, Context Broker IP, and project name. You can provide these through a configuration file or as arguments when initializing the artifacts.

## Compatibility

These artifacts are compatible with both Orion and Scorpio Context Brokers, allowing you to work with either implementation of the NGSI-LD API.

## Documentation

For detailed documentation, please visit our [Wiki