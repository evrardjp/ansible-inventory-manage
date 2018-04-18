""" Global testing fixtures """
import pytest
import json
import ansible_inventory_manage.inventory

inventory_file = 'tests/small.json'

@pytest.fixture()
def inventoryloader():
    """
    Loads a standard inventory that
    can be used for manipulations
    """
    with open(inventory_file, 'r') as fd:
        fc =json.loads(fd.read())
    inventoryloader = ansible_inventory_manage.inventory.Inventory()
    inventoryloader.load_inventoryjson(fc)
    return inventoryloader
