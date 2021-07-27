# Charm-Algorand-Node

## Description
The Algorand Node Charm is a Juju Charm for faciliting deployment and maintenance of an Algorand participation node within production cloud environments. 

To get started using Juju follow instructions [here](https://juju.is/docs/olm/create-controllers) to bootstrap Juju. In a nutshell:
1) Create a cloud controller for your desired cloud provider (ie, GCP, AWS, Azure, Localhost/LXD, etc)
2) Create a model
3) Deploy Algorand Node via this charm to the model

## Usage

Deploy to desired cloud and allow node to catch up.

    juju deploy algorand-node

Run action to **check node status** or to **trigger fast catchup**:

    juju run-action algonode/0 check-node-status --wait
    juju run-action algonode/0 fast-catchup --wait

Get Node URL and Token via Relation with other Apps or by Action:

**TODO**

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

Run all tests with `run_tests`:

    ./run_tests

Run specific test types with `tox`:

    tox -e lint
    tox -e unit
    tox -e functional

## Links
[Juju Create Controller](https://juju.is/docs/olm/create-controllers) \
[Full Node Configuration Settings](https://developer.algorand.org/docs/reference/node/config/)

