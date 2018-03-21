import pytest
from ansible_inventory_manage.inventory import Host, Group, Inventory
import ansible_inventory_manage.inventory 


def create_objects():
    groupa, groupb = Group(groupname='groupa'), Group(groupname='groupb')
    hosta, hostb = Host('hosta'), Host('hostb')
    return (hosta, hostb, groupa, groupb)


testmergedicts_data=[
    (
        dict(a='a'),
        dict(b='b'),
        (0,0),
        dict(a='a',b='b')
    ),
    #test simple conflict merge
    (
        dict(a='a'),
        dict(a='b'),
        (0,0),
        dict(a='a')
    ),
    # test first level of precedence
    (
        dict(a='a'),
        dict(a='b'),
        (0,1),
        dict(a='b')
    ),
    # test normal precedence with non zero values
    (
        dict(a='a'),
        dict(a='b'),
        (2,1),
        dict(a='a')
    ),
    # test negative values for precedences
    (
        dict(a='a'),
        dict(a='b'),
        (-1,0),
        dict(a='b')
    ),
    # test sub dict std merge
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeyb='b')),
        (0,0),
        dict(a=dict(subkeya='a',subkeyb='b'))
    ),
    # test subdict std precedence
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeya='b')),
        (0,0),
        dict(a=dict(subkeya='a'))
    ),
    # test subdict keeps prios
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeya='b')),
        (-1,0),
        dict(a=dict(subkeya='b'))
    ),
    # test subdict keep prios (inverse prio as previous test)
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeya='b')),
        (1,0),
        dict(a=dict(subkeya='a'))
    ),
    # test subdict for values that aren't dicts
    (
        dict(a=dict(subkeya=1)),
        dict(a=dict(subkeya=2)),
        (0,0),
        dict(a=dict(subkeya=1))
    ),
    # test subdict for values that aren't dicts or lists with prios
    (
        dict(a=dict(subkeya=1)),
        dict(a=dict(subkeya=2)),
        (0,1),
        dict(a=dict(subkeya=2))
    ),
    # test subdict for list values
    (
        dict(a=dict(subkeya=[1])),
        dict(a=dict(subkeya=[2])),
        (0,1),
        dict(a=dict(subkeya=[1,2]))
    ),
    # complex example with multiples levels and overlaps
    (
        dict(a=dict(subkeya=dict(subsuba='a',subsubc='c'), subkeyb='b',subkeyc='c'),c='c'),
        dict(a=dict(subkeya=dict(subsuba='b'),subkeyb='override'),b='b'),
        (0,1),
        dict(a=dict(subkeya=dict(subsuba='b',subsubc='c'),subkeyb='override',subkeyc='c'),b='b',c='c')
    ),
    # complex example with multiples levels and overlaps - reversed
    (
        dict(a=dict(subkeya=dict(subsuba='b'),subkeyb='override'),b='b'),
        dict(a=dict(subkeya=dict(subsuba='a',subsubc='c'), subkeyb='b',subkeyc='c'),c='c'),
        (1,0),
        dict(a=dict(subkeya=dict(subsuba='b',subsubc='c'),subkeyb='override',subkeyc='c'),b='b',c='c')
    ),
]

@pytest.mark.parametrize("a,b,prios,expected", testmergedicts_data)
def test_mergedicts(a, b, prios, expected):
    result = ansible_inventory_manage.inventory.mergedicts(a, b, prios)
    assert dict(result) == expected


# Test hosts changes
class TestHost(object):
    def test_create(self):
        a = Host('a')
        assert a.hostname == 'a'
        assert a.hostvars == dict()
        
        hostvars = dict(bidule='machin')
        b = Host('b', hostvars)
        assert b.hostvars['bidule'] == 'machin'

    def test_add_group(self):
        hosta, hostb, groupa, _ = create_objects()
        hosta.add_group(groupa)
        hostb.add_group(groupa)
        assert hosta in groupa.hosts
        assert hostb in groupa.hosts
        assert groupa in hosta.groups
        return (hosta, hostb, groupa)

    def test_remove_group(self):
        hosta, hostb, groupa = self.test_add_group()
        hosta.del_group(groupa)
        assert hosta not in groupa.hosts
        assert groupa not in hosta.groups
        # check hostb wasn't modified by any chance
        assert hostb in groupa.hosts
        assert groupa in hostb.groups
        # Ensure no exception is thrown
        hosta.del_group(groupa)

    def test_rename(self):
        hosta, _, groupa, _ = create_objects()
        hosta.hostname = 'babar'
        hosta.add_group(groupa)
        assert groupa.hosts[0].hostname == 'babar'

    def test_delete(self):
        pass

    def test_update_hostvar(self):
        pass


class TestGroup(object):
    def test_create(self):
        a = Group('a')
        assert a.groupname == 'a'

        groupvars = dict(babar='woot')
        a = Group('b', groupvars=groupvars)
        assert a.groupvars['babar'] == 'woot'

    def test_repr(self):
        a = Group('a')
        assert str(a) == "Group(groupname='a')"
        
    def test_add_parent(self):
        """ Adds the groupb as parent of groupa """
        _, _, groupa, groupb = create_objects()
        groupa.add_parent(groupb)
        assert groupb in groupa.parents
        assert groupa in groupb.children
        return (groupa, groupb)

    def test_remove_parent(self):
        """ Removes groupb of previous set of parents """
        groupa, groupb = self.test_add_parent()
        groupa.del_parent(groupb)
        assert groupb not in groupa.parents
        assert groupa not in groupb.children

    def test_replace_parent(self):
        """ Groupc replaces groupb """
        _, _, groupa, groupb = create_objects()
        groupc = Group('groupc')
        groupa.add_parent(groupb)
        groupa.replace_parent(groupb, groupc)
        assert groupc in groupa.parents
        assert groupb not in groupa.parents
        assert groupa in groupc.children
        assert groupa not in groupb.children

    def test_rename(self):
        a, b = self.test_add_parent()
        a.groupname = 'newgroupname'
        assert b.children[0].groupname == 'newgroupname'

    def test_delete(self):
        a, b = self.test_add_parent()
        b.delete()
        assert a.parents == []
        # del b
        # stdout, stderr = capfd.readouterr()
        # assert "Deleting myself" in stdout

    def test_update_groupvar(self):
        pass

    def test_reorder_parents(self):
        pass

    def test_reorder_children(self):
        pass


# Inventory
class TestInventory(object):
    def test_loadjson(self):
        """
        Deserializes a json file, and
        checks if the inventory is as expected
        """
        pass

    def test_new_group(self):
        """
        Ensure you can add a group to the inventory
        """
        pass

    def test_add_existing_group(self):
        """
        Adding a group with the same name as an
        existing one should update the existing
        by default
        """
        pass

    def test_add_existing_group_unauthorized(self):
        """
        Do not add a group if it's already existing
        """
        pass

    def test_delete_group(self):
        pass

    def test_rename_group(self):
        pass

    def test_set_priority(self):
        pass

    def test_add_host(self):
        pass

    def test_remove_host(self):
        pass

    def test_rename_host(self):
        pass

    def test_modify_groupvars(self):
        pass

    def test_modify_hostvars(self):
        pass

    def test_deserialize(self):
        pass

    def test_flatten_inventory(self):
        pass

