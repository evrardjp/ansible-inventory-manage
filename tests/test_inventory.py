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
        pass

    def test_set_vars(self):
        hostvars = dict(bidule='machin')
        b = Host('b')
        b.set_vars(hostvars)
        assert b.vars['bidule'] == 'machin'


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

    def test_remove_parent(self):
        """ Removes groupb of previous set of parents """
        groupa, groupb = self.test_add_parent()
        groupa.del_parent(groupb)
        assert groupb not in groupa.parents
        assert groupa not in groupb.children

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

    def test_delete(self):
        a, b = self.test_add_parent()
        b.delete()
        assert a.parents == []
        # del b
        # stdout, stderr = capfd.readouterr()
        # assert "Deleting myself" in stdout

    def test_delete_with_reparent(self):
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

    def test_variables_are_saved_when_delete_with_reparent(self):
        child1, child2 = Group(name='child1'), Group(name='child2')
        mid = Group(name='mid')
        mid.vars['groupvarname'] = 'value'
        parent1, parent2 = Group(name='par'), Group(name='par2')
        for child in [child1, child2]:
            child.add_parent(mid)
        for par in [parent1, parent2]:
            mid.add_parent(par)
        mid.delete(reparent_groups=True, reparent_vars=True)
        for child in [child1, child2]:
            assert parent1 in child.parents
            assert parent2 in child.parents
            assert mid not in child.parents
        for parent in [parent1, parent2]:
            assert parent.vars['groupvarname'] == 'value'

    def test_update_groupvar(self):
        pass

    def test_reorder_parents(self):
        pass

    def test_reorder_children(self):
        pass

    def test_add_child(self):
        pass

    def test_add_self_as_child(self):
        pass

    def test_remove_child(self):
        pass

    def test_replace_child(self):
        pass

    def test_remove_self_as_child(self):
        pass

    def test_has_cyle(self):
        pass

    def test_has_no_cycle(self):
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
