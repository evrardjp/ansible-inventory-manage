import itertools
import copy


from ansible_inventory_manage.names import Hostname, Groupname, Varname


def mergedicts(dict1, dict2, prios=(0, 0)):
    """
    Merges dict2 into dict1 together.
    In case of ties, prios (dict1, dict2) determines the winner
    """
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(mergedicts(dict1[k], dict2[k], prios)))
            else:
                if isinstance(dict1[k], list) and isinstance(dict2[k], list):
                    # We can merge further, by merging lists.
                    list1 = copy.deepcopy(dict1[k])
                    list1.extend(copy.deepcopy(dict2[k]))
                    yield (k, list1)
                # If one of the values is not a dict, you can't
                # continue merging it.
                # Take the one who has the higher prio.
                elif prios[0] < prios[1]:
                    yield (k, dict2[k])
                else:
                    yield (k, dict1[k])
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])


def change_element_index(listname, oldindex, newindex):
    """
    This method is used to modify the order,
    by changing an item from its old position
    to a new position, keeping the rest of the
    list intact. This is useful for altering the
    group variable flattening: the flattening is done by
    browsing the lists. (Last match wins if tie)
    """
    listname.insert(newindex, listname.pop(oldindex))
    return listname


class InventoryObject(object):
    def __init__(self):
        self.vars = {}
        self.priority = 0

    def set_var(self, varname, value):
        self.vars[varname] = value

    def set_vars(self, vardict, prio=0):
        self.vars = dict(
            mergedicts(self.vars, vardict, (self.priority, prio))
        )


class Group(InventoryObject):
    """ A group of hosts, groups, and/or vars"""

    __slots__ = ['name', 'vars', 'children', 'parents',
                 'hosts', 'priority']

    def __init__(self, name=None):
        super(Group, self).__init__()
        if not Groupname.is_valid_name(name):
            raise Exception("Not a valid name")
        else:
            self.name = name
        self.children = []
        # Parents is not an ansible information, but it's useful for
        # global loop avoidance when deleting/renaming things.
        self.parents = []
        self.hosts = []
        # For VARIABLE precedence resolving, we introduce a priority.
        self.priority = 0

    def __repr__(self):
        return "Group(name='%s')" % (self.name)

    def add_parent(self, parent):
        if parent is self:
            raise Exception("Cannot add yourself as parent")
        if parent not in self.parents:
            self.parents.append(parent)
        if self not in parent.children:
            parent.children.append(self)

    def del_parent(self, parent):
        if parent in self.parents:
            self.parents.remove(parent)
        if self in parent.children:
            parent.children.remove(self)

    def replace_parent(self, oldparent, newparent):
        """ Switch parents to change inheritence """
        oldparent.del_child(self)
        newparent.add_child(self)

    def add_child(self, child):
        if child is self:
            raise Exception("Cannot add yourself as child")
        if child not in self.children:
            self.children.append(child)
        if self not in child.parents:
            child.parents.append(self)

    def del_child(self, child):
        if child in self.children:
            self.children.remove(child)
        if self in child.parents:
            child.parents.remove(self)

    def replace_child(self, oldchild, newchild):
        oldchild.del_parent(self)
        newchild.add_parent(self)

    def add_host(self, host):
        if host not in self.hosts:
            self.hosts.append(host)
        if self not in host.groups:
            host.groups.append(self)

    def del_host(self, host):
        if host in self.hosts:
            self.hosts.remove(host)
        if self in host.groups:
            host.groups.remove(self)

    def reorder_children(self, oldindex, newindex):
        """
        The children are a list, and
        remember the order of inclusion.
        """
        self.children = change_element_index(
            self.children,
            oldindex,
            newindex
        )

    def reorder_parents(self, oldindex, newindex):
        """
        The parents are a list, and
        remember the order of inclusion.
        This method is used to modify the order of
        the parents, changing an item position from
        oldindex to new index, keeping the rest of
        the list intact. This is useful for altering
        the group variables, which alter their
        rendering values when doing the last
        host flattening (Last match wins if tie).
        """
        self.parents = change_element_index(
            self.parents,
            oldindex,
            newindex
        )

    def delete(self, reparent_groups=False, reparent_vars=False):
        if reparent_vars:
            for parent in self.parents:
                parent.set_vars(self.vars, self.priority)
        while len(self.children) != 0:
            if reparent_groups:
                for parent in self.parents:
                    self.children[0].add_parent(parent)
            self.children[0].del_parent(self)
        while len(self.parents) != 0:
            self.parents[0].del_child(self)
        while len(self.hosts) != 0:
            self.hosts[0].del_group(self)


class Host(InventoryObject):
    def __init__(self, name=None):
        if not Hostname.is_valid_name(name):
            raise Exception("Hostname cannot be empty")
        else:
            self.name = name
        super(Host, self).__init__()
        self.vars = {}
        self.groups = []

    def __repr__(self):
        return "Host(name='%s')" % (self.name)

    def add_group(self, group):
        group.add_host(self)

    def del_group(self, group):
        group.del_host(self)

    def reorder_groups(self, oldindex, newindex):
        pass

    def delete(self):
        while len(self.groups) != 0:
            group = self.groups[0]
            print("current group is %s" % group)
            group.del_host(self)
            print("current group list %s" % self.groups)
            print("end of iteration, next!")
        print("done")


class Inventory(object):
    def __init__(self):
        self.groups = {}
        self.hosts = {}

    def load_inventoryjson(self, jsoncontent):
        # _meta is the only information outside group data
        hosts_metadata = jsoncontent.pop('_meta')
        for hostname, hostvars in hosts_metadata['hostvars'].items():
            self.add_host(hostname, hostvars)

        # group data is structured in json file as
        # groupname: {"children":[], "hosts": []}
        for groupname, groupinfo in jsoncontent.items():
            # Discover groups and their structure
            self.add_group(groupname, groupinfo)

    def add_group(self, groupname, groupinfo=None, allow_update=True):
        """ Add group will be called with an update or not update
        mode, depending on the situation, to add a group to the
        inventory
        """
        is_new_group = False
        if groupname not in self.groups.keys():
            is_new_group = True
        if is_new_group or allow_update:
            self._process_groupadd(groupname, groupinfo, is_new_group)
        elif groupinfo:
            # The group exists AND the updates are not allowed
            raise KeyError

    def _process_groupadd(self, groupname, groupinfo=None, is_new_group=False):
        for subgroup in itertools.chain(
                groupinfo.get('children', []),
                groupinfo.get('parents', [])):
            self.add_group(subgroup)
        priority = groupinfo.get('priority', 0)
        if is_new_group:
            self.groups[groupname] = Group(groupname=groupname)
            # Don't update priority when updating an existing group, unless
            # explicity told so in a separate function
            self.set_group_priority(groupname, priority)
        # Now proceed with hierarchy, merging the new (if any) to the existing.
        for child in groupinfo.get('children', []):
            self.groups[groupname].add_child(self.groups[child])
        for parent in groupinfo.get('parents', []):
            self.groups[groupname].add_parent(self.groups[parent])
        for new_vars in \
                groupinfo.get('vars', {}), groupinfo.get('vars', {}):

            result = mergedicts(self.groups[groupname].vars,
                                new_vars,
                                prios=(self.groups[groupname].priority,
                                       priority
                                       )
                                )
            self.groups[groupname].vars = dict(result)

    def del_group(self, groupname, reparent=False):
        pass

    def rename_group(self, groupname, newgroupname):
        pass

    def set_group_priority(self, groupname, priority):
        """ Allows the user to set a priority to a group, for variable
        merging purposes
        """
        self.groups[groupname].priority = priority

    def add_host(self, hostname=None, hostvars=None, allow_update=True):
        pass

    def del_host(self):
        pass

    def rename_host(self):
        pass
