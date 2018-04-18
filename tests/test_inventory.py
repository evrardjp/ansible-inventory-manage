import json
import pytest
from ansible_inventory_manage.inventory import Host, Group, Inventory
from ansible_inventory_manage.inventory import InventoryObject
import ansible_inventory_manage.inventory


def create_objects():
    groupa, groupb = Group(name='groupa'), Group(name='groupb')
    hosta, hostb = Host('hosta'), Host('hostb')
    return (hosta, hostb, groupa, groupb)

testmergedicts_data = [
    (
        dict(a='a'),
        dict(b='b'),
        (0, 0),
        dict(a='a', b='b')
    ),
    # test simple conflict merge
    (
        dict(a='a'),
        dict(a='b'),
        (0, 0),
        dict(a='a')
    ),
    # test first level of precedence
    (
        dict(a='a'),
        dict(a='b'),
        (0, 1),
        dict(a='b')
    ),
    # test normal precedence with non zero values
    (
        dict(a='a'),
        dict(a='b'),
        (2, 1),
        dict(a='a')
    ),
    # test negative values for precedences
    (
        dict(a='a'),
        dict(a='b'),
        (-1, 0),
        dict(a='b')
    ),
    # test dict is dropping its k/v
    (
        dict(a='a'),
        dict(b='b'),
        (-999, 0),
        dict(b='b')
    ),
    # test dict is dropping its k/v
    (
        dict(a='a'),
        dict(b='b'),
        (0, -999),
        dict(a='a')
    ),
    # test dict is dropping its k/v
    (
        dict(a='a'),
        dict(b='b'),
        (-999, -999),
        dict()
    ),
    # test sub dict std merge
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeyb='b')),
        (0, 0),
        dict(a=dict(subkeya='a', subkeyb='b'))
    ),
    # test subdict std precedence
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeya='b')),
        (0, 0),
        dict(a=dict(subkeya='a'))
    ),
    # test subdict keeps prios
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeya='b')),
        (-1, 0),
        dict(a=dict(subkeya='b'))
    ),
    # test subdict keep prios (inverse prio as previous test)
    (
        dict(a=dict(subkeya='a')),
        dict(a=dict(subkeya='b')),
        (1, 0),
        dict(a=dict(subkeya='a'))
    ),
    # test subdict for values that aren't dicts
    (
        dict(a=dict(subkeya=1)),
        dict(a=dict(subkeya=2)),
        (0, 0),
        dict(a=dict(subkeya=1))
    ),
    # test subdict for values that aren't dicts or lists with prios
    (
        dict(a=dict(subkeya=1)),
        dict(a=dict(subkeya=2)),
        (0, 1),
        dict(a=dict(subkeya=2))
    ),
    # test subdict for list values
    (
        dict(a=dict(subkeya=[1])),
        dict(a=dict(subkeya=[2])),
        (0, 1),
        dict(a=dict(subkeya=[1, 2]))
    ),
    # complex example with multiples levels and overlaps
    (
        dict(a=dict(subkeya=dict(subsuba='a', subsubc='c'),
                    subkeyb='b', subkeyc='c'), c='c'),
        dict(a=dict(subkeya=dict(subsuba='b'), subkeyb='override'), b='b'),
        (0, 1),
        dict(a=dict(subkeya=dict(subsuba='b', subsubc='c'),
                    subkeyb='override', subkeyc='c'), b='b', c='c')
    ),
    # complex example with multiples levels and overlaps - reversed
    (
        dict(a=dict(subkeya=dict(subsuba='b'), subkeyb='override'), b='b'),
        dict(a=dict(subkeya=dict(subsuba='a', subsubc='c'),
                    subkeyb='b', subkeyc='c'), c='c'),
        (1, 0),
        dict(a=dict(subkeya=dict(subsuba='b', subsubc='c'),
                    subkeyb='override', subkeyc='c'), b='b', c='c')
    ),
]

@pytest.mark.parametrize("a,b,prios,expected", testmergedicts_data)
def test_mergedicts(a, b, prios, expected):
    result = ansible_inventory_manage.inventory.mergedicts(a, b, prios)
    assert dict(result) == expected

def test_merge_dicts_with_invalid_prios():
    a = {'a', '1'}
    b = {'a': '3'}
    with pytest.raises(TypeError):
        dict(ansible_inventory_manage.inventory.mergedicts(a, b, prios=('a', 'b')))

class TestInventoryObject(object):
    def test_change_element_index(self):
        assert ['b', 'a', 'c'] == \
            InventoryObject.change_element_index(['a', 'b', 'c'], 1, 0)


# Test hosts changes
class TestHost(object):
    def test_create(self):
        a = Host('a')
        assert a.name == 'a'
        assert a.vars == dict()

        b = Host(name='a')
        assert b.name == 'a'
        assert b.vars == dict()

    def test_show_host(self):
        a = Host(name='a')
        assert a.__repr__() == "Host(name='a')"

    def test_create_with_no_hostname(self):
        with pytest.raises(Exception):
            Host()

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
        hosta.name = 'babar'
        hosta.add_group(groupa)
        assert groupa.hosts[0].name == 'babar'

    def test_delete(self):
        hosta = Host('hosta')
        groupa = Group('groupa')
        groupb = Group('groupb')
        hosta.add_group(groupa)
        hosta.add_group(groupb)
        hosta.delete()
        assert len(groupa.hosts) == 0
        assert len(groupb.hosts) == 0

    def test_update_hostvar(self):
        hosta = Host('hosta')
        hosta.set_var('a', 'valuea')
        assert hosta.vars['a'] == 'valuea'

    def test_set_vars(self):
        hostvars = dict(bidule='machin')
        b = Host('b')
        b.set_vars(hostvars)
        assert b.vars['bidule'] == 'machin'

    def test_reorder_groups(self):
        a, b = Group('a'), Group('b')
        h1 = Host('h1')
        h1.add_group(a)
        h1.add_group(b)
        h1.reorder_groups(1,0)
        assert h1.groups[0].name == 'b'
        assert h1.groups[1].name == 'a'

    def test_has_group(self):
        g1, h1 = Group('g1'), Host('h1')
        g1.add_host(h1)
        assert h1.has_group('g1')
        assert not h1.has_group('u2')


class TestGroup(object):
    def test_create(self):
        a = Group('a')
        assert a.name == 'a'

    def test_set_var(self):
        a = Group('a')
        a.set_var('babar', 'woot')
        assert a.vars['babar'] == 'woot'

    def test_set_vars(self):
        a = Group('a')
        gvars = dict(babar='woot')
        a.set_vars(gvars)
        assert a.vars['babar'] == 'woot'

    def test_create_with_no_groupname(self):
        with pytest.raises(Exception):
            Group()

    def test_repr(self):
        a = Group('a')
        assert str(a) == "Group(name='a')"

    def test_add_parent(self):
        """ Adds the groupb as parent of groupa """
        _, _, groupa, groupb = create_objects()
        groupa.add_parent(groupb)
        assert groupb in groupa.parents
        assert groupa in groupb.children
        return (groupa, groupb)

    def test_add_self_as_parent(self):
        """ You should not create direct loops.
            That's not good """
        groupa = Group('groupa')
        with pytest.raises(Exception):
            groupa.add_parent(groupa)

    def test_add_invild_parent(self):
        groupa = Group('groupa')
        with pytest.raises(TypeError):
            groupa.add_parent("babar")

    def test_remove_parent(self):
        """ Removes groupb of previous set of parents """
        groupa, groupb = self.test_add_parent()
        groupa.del_parent(groupb)
        assert groupb not in groupa.parents
        assert groupa not in groupb.children

    def test_remove_invalid_parent(self):
        groupa, _ = self.test_add_parent()
        with pytest.raises(TypeError):
            groupa.del_parent("babar")

    def test_remove_self_as_parent(self):
        """
        Removing yourself as parent should
        not throw any exception.
        """
        groupa, groupb = Group('groupa'), Group('groupb')
        groupa.add_parent(groupb)
        groupb.del_parent(groupb)

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

    def test_replace_parent_to_self(self):
        """ You tricky basterd. Should fail """
        groupa, groupb = Group('groupa'), Group('groupb')
        groupa.add_parent(groupb)
        with pytest.raises(Exception):
            groupa.replace_parent(groupb, groupa)

    def test_rename(self):
        a, b = self.test_add_parent()
        a.name = 'newgroupname'
        assert b.children[0].name == 'newgroupname'

    def test_delete_no_reparent(self):
        a, b = self.test_add_parent()
        b.delete()
        assert a.parents == []
        # del b
        # stdout, stderr = capfd.readouterr()
        # assert "Deleting myself" in stdout

    def test_delete_reparent_groups(self):
        child1, child2 = Group(name='child1'), Group(name='child2')
        mid = Group(name='mid')
        parent1, parent2 = Group(name='par'), Group(name='par2')
        for child in [child1, child2]:
            child.add_parent(mid)
        for par in [parent1, parent2]:
            mid.add_parent(par)
        mid.delete(reparent_groups=True)
        for child in [child1, child2]:
            assert parent1 in child.parents
            assert parent2 in child.parents
            assert mid not in child.parents

    def test_delete_reparent_hosts(self):
        g1, g2 = Group(name='todelete'), Group(name='parent')
        host1 = Host(name='host')
        host1.add_group(g1)
        g1.add_parent(g2)
        g1.delete(reparent_hosts=True)
        assert g2 in host1.groups
        assert g1 not in host1.groups

    def test_delete_reparent_vars(self):
        child1, child2 = Group(name='child1'), Group(name='child2')
        mid = Group(name='mid')
        mid.vars['groupvarname'] = 'value'
        parent1, parent2 = Group(name='par'), Group(name='par2')
        for child in [child1, child2]:
            child.add_parent(mid)
        for par in [parent1, parent2]:
            mid.add_parent(par)
        mid.delete(reparent_vars=True)
        for parent in [parent1, parent2]:
            assert parent.vars['groupvarname'] == 'value'

    def test_update_groupvar(self):
        gr1 = Group(name='g1')
        gr1.vars['a'] = 'va'
        gr1.set_var('b', 'vb')
        assert gr1.vars == {'a': 'va', 'b': 'vb'}

    def test_add_child(self):
        child1, a = Group(name='child1'), Group(name='a')
        a.add_child(child1)
        assert a.children[0].name == 'child1'

    def test_add_invalidchild(self):
        a = Group(name='a')
        with pytest.raises(TypeError):
            a.add_child("bazar")

    def test_add_self_as_child(self):
        a = Group(name='a')
        with pytest.raises(Exception):
            a.add_child(a)

    def test_remove_child(self):
        child1, a = Group(name='child1'), Group(name='a')
        a.add_child(child1)
        assert a.children[0].name == 'child1'
        a.del_child(child1)

    def test_remove_invalid_child(self):
        child1, a = Group(name='child1'), Group(name='a')
        a.add_child(child1)
        assert a.children[0].name == 'child1'
        with pytest.raises(TypeError):
            a.del_child("qw")

    def test_remove_notpresent_child(self):
        child1, a = Group(name='child1'), Group(name='a')
        a.add_child(child1)
        assert a.children[0].name == 'child1'
        a.del_child(child1)
        assert len(a.children) == 0
        try:
            a.del_child(child1)
        except Exception:
            raise pytest.fail("Should not failed")

    def test_replace_child(self):
        child1, child2 = Group(name='child1'), Group(name='child2')
        mid = Group(name='mid')
        mid.add_child(child1)
        mid.replace_child(child1, child2)
        assert mid.children[0].name == 'child2'

    def test_has_cyle(self):
        pass

    def test_has_no_cycle(self):
        pass

    def test_reorder_parents(self):
        parent1, parent2 = Group(name='par1'), Group(name='par2')
        a = Group('a')
        a.add_parent(parent1)
        a.add_parent(parent2)
        a.reorder_parents(1, 0)
        assert a.parents[0].name == 'par2'
        assert a.parents[1].name == 'par1'

    def test_reorder_children(self):
        child1, child2 = Group(name='child1'), Group(name='child2')
        a = Group('a')
        a.add_child(child1)
        a.add_child(child2)
        a.reorder_children(1, 0)
        assert a.children[0].name == 'child2'
        assert a.children[1].name == 'child1'

    def test_add_invalid_host(self):
        groupa = Group('groupa')
        with pytest.raises(TypeError):
            groupa.add_host('a')

    def test_add_host(self):
        groupa = Group('groupa')
        hosta = Host('a')
        groupa.add_host(hosta)
        assert groupa.hosts[0].name == 'a'

    def test_remove_host(self):
        groupa = Group('groupa')
        hosta = Host('a')
        groupa.add_host(hosta)
        assert groupa.hosts[0].name == 'a'
        groupa.del_host(hosta)
        assert len(groupa.hosts) == 0

    def test_remove_invalid_host(self):
        groupa = Group('groupa')
        with pytest.raises(TypeError):
            groupa.del_host('q')

    def test_remove_no_host_anymore(self):
        groupa = Group('groupa')
        hosta = Host('a')
        groupa.add_host(hosta)
        assert groupa.hosts[0].name == 'a'
        groupa.del_host(hosta)
        groupa.del_host(hosta)

    def test_remove_group_from_hosts(self):
        groupa = Group('groupa')
        hosta, hostb = Host('a'), Host('b')
        hosta.add_group(groupa)
        hostb.add_group(groupa)
        assert len(groupa.hosts) == 2
        groupa.delete()
        assert len(hosta.groups) == 0
        assert len(hostb.groups) == 0

    def test_has_host(self):
        g1, h1  = Group('g1'), Host('h1')
        g1.add_host(h1)
        assert g1.has_host(u'h1')
        assert g1.has_host('h1')
        assert not g1.has_host('u2')

    def test_has_group(self):
        g1, g2, g3 = Group('g1'), Group('g2'), Group('g3')
        g2.add_child(g1)
        g2.add_parent(g3)
        assert g1.has_group("g2")
        assert g2.has_group("g1")
        assert g2.has_group("g3")
        assert g3.has_group("g2")
        assert not g3.has_group('u2')



# Inventory
inventory_data =[
    (
        'tests/simple.json',
        [],
        ['localhost'],
    ),
    (
        'tests/small.json',
        ['glance_all', 'glance_api', 'glance_registry'],
        ['localhost', 'localhost2'],
    ),
]
class TestInventory(object):
    @pytest.mark.parametrize("fname,groups,hosts", inventory_data)
    def test_input_loadjson(self, fname, groups, hosts):
        """
        Deserializes a json file, and
        checks if the inventory is as expected
        """
        with open(fname,'r') as fd:
            fcon = json.loads(fd.read())
        inventory = Inventory()
        inventory.load_inventoryjson(fcon)
        assert inventory.count_groups() == len(groups)
        assert inventory.count_hosts() == len(hosts)

    def test_new_group(self, inventoryloader):
        """
        Ensure you can add a group to the inventory
        """
        inventoryloader.add_group(u'newgroup')
        assert 'newgroup' in inventoryloader.groups

    def test_add_existing_group(self, inventoryloader):
        """
        Adding a group with the same name as an
        existing one should update the existing
        by default
        """
        grp_cnt = inventoryloader.count_groups()
        grp_vars = inventoryloader.groups['glance_api'].vars
        inventoryloader.add_group(u'glance_api')
        assert inventoryloader.count_groups() == grp_cnt
        assert inventoryloader.groups['glance_api'].vars == grp_vars
        assert 'br-mgmt' == inventoryloader.groups['glance_api'].vars['management_bridge']
        inventoryloader.add_group(u'glance_api', {"vars": { u'external_bridge': u'br-ext'}})
        assert 'br-mgmt' == inventoryloader.groups['glance_api'].vars['management_bridge']
        assert 'br-ext' == inventoryloader.groups['glance_api'].vars['external_bridge']


    def test_add_existing_group_unauthorized(self, inventoryloader):
        """
        Do not add a group if it's already existing
        if allow_update is set to False
        and some variables are set.
        """
        assert 'glance_api' in inventoryloader.groups
        glance_group = {'vars':{'glance_api_version': '2'} }
        with pytest.raises(ValueError):
            inventoryloader.add_group(u'glance_api', groupinfo=glance_group,
                                      allow_update=False)

    def test_add_existing_emptygroup_unauthorized(self, inventoryloader):
        """
        Do not throw an exception if the new group to add has no var
        """
        assert 'glance_api' in inventoryloader.groups
        inventoryloader.add_group(u'glance_api', allow_update=False)
        # but ensures variables didn't get overriden
        assert 'management_bridge' in inventoryloader.groups['glance_api'].vars

    def test_delete_group(self, inventoryloader):
        """
        Ensures a group can be deleted, no reparenting at all
        """
        cg = inventoryloader.count_groups()
        ch = inventoryloader.count_hosts()
        inventoryloader.del_group('glance_api')
        assert 'glance_api' not in inventoryloader.groups['glance_all'].children
        assert 'glance_api' not in inventoryloader.hosts['localhost'].groups
        assert 'glance_api' not in inventoryloader.groups
        assert inventoryloader.count_groups() == cg -1
        assert inventoryloader.count_hosts() == ch
    
    def test_delete_group_reparent_hosts(self, inventoryloader):
        """
        Ensures the hosts of a group find a new parent
        """
        inventoryloader.del_group('glance_api', reparent_hosts=True)
        assert inventoryloader.groups['glance_all'].has_host('localhost')
        assert inventoryloader.hosts['localhost'].has_group('glance_all')

    def test_delete_group_reparent_groups(self, inventoryloader):
        """
        Ensures the hosts of a group find a new parent
        """
        inventoryloader.del_group('glance_all', reparent_groups=True)
        assert inventoryloader.groups['glance_api'].has_group('all')
        assert inventoryloader.groups['all'].has_group('glance_api')

    def test_delete_group_reparent_vars(self, inventoryloader):
        """
        Ensures the hosts of a group find a new parent
        """
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

    def test_change_ip(self):
        pass

    def test_deserialize(self):
        pass

    def test_flatten_inventory(self):
        pass

    def test_io_equal(self):
        """ Ensures that parsing the inventory
        and outputting it without manipulation doesn't
        change the structure
        """
        pass

    def test_output_has_hostvars(self):
        pass

    def test_output_has_all_group(self):
        pass

    def test_output_has_expected_groups_present(self):
        pass

    def test_output_has_only_expected_groups(self):
        """ Computes the number of groups, and compares
        to expected value
        """
        pass

    def test_output_has_expected_hostvar(self):
        pass

    def test_output_has_expected_hosts(self):
        pass

    def test_output_has_only_expected_hosts(self):
        """ Computes the number of hosts, and compares
        to expected value
        """
        pass

    def test_output_has_expected_groups_for_host(self):
        pass

    def test_output_has_no_group_twice(self):
        pass

    def test_output_has_no_host_twice(self):
        pass
