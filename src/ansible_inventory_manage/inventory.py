import itertools
import copy


from past.builtins import basestring    # pip install future

def is_valid_name(name=None):
    if name and isinstance(name, basestring):
        return True
    else:
        return False


def is_valid_host(name=None):
    if is_valid_name(name) and \
       len(name) < 253 and \
       name.replace('_', '').replace('-', '').replace('.', '').isalnum():
        return True
    else:
        return False


def mergedicts(dict1, dict2, prios=(0, 0)):
    """
    Merges dict2 into dict1 together.
    In case of ties, prios (dict1, dict2) determines the winner.
    Prios are integer.
    A prio of -999 "nein nein nein" means dropping the var.
    """
    if not isinstance(prios[0], int) or not isinstance(prios[1], int):
        raise TypeError("Prios must be integers")
    if prios[0] == -999:
        dict1 = {}
    if prios[1] == -999:
        dict2 = {}
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


class InventoryObject(object):
    def __init__(self, name=None):
        self.name = name
        self.vars = {}
        # For VARIABLE precedence resolving, we introduce a priority.
        self.priority = 0

    def __repr__(self):
        return ("%s(name='%s')" % (self.__class__.__name__, self.name))

    def set_var(self, varname, value):
        self.vars[varname] = value

    def set_vars(self, newvars, prio=0):
        self.vars = dict(
            mergedicts(self.vars, newvars, (self.priority, prio))
        )

    @staticmethod
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


class Group(InventoryObject):
    """ A group of hosts, groups, and/or vars"""

    __slots__ = ['name', 'vars', 'children', 'parents',
                 'hosts', 'priority']

    def __init__(self, name=None):
        if not is_valid_name(name):
            raise Exception("Not a valid name")
        else:
            super(Group, self).__init__(name)
        self.children = []
        # Parents is not an ansible information, but it's useful for
        # global loop avoidance when deleting/renaming things.
        self.parents = []
        self.hosts = []

    def add_parent(self, parent):
        if parent is self:
            raise Exception("Cannot add yourself as parent")
        if not isinstance(parent, Group):
            raise TypeError("%s is not a group" % parent)
        if parent not in self.parents:
            self.parents.append(parent)
        if self not in parent.children:
            parent.children.append(self)

    def del_parent(self, parent):
        if not isinstance(parent, Group):
            raise TypeError("%s is not a group" % parent)
        if parent in self.parents:
            self.parents.remove(parent)
        if self in parent.children:
            parent.children.remove(self)

    def replace_parent(self, oldparent, newparent):
        """ Switch parents to change inheritence """
        oldparent.del_child(self)
        newparent.add_child(self)

    def add_child(self, child):
        if not isinstance(child, Group):
            raise TypeError("%s is not a group" % child)
        if child is self:
            raise Exception("Cannot add yourself as child")
        if child not in self.children:
            self.children.append(child)
        if self not in child.parents:
            child.parents.append(self)

    def del_child(self, child):
        if not isinstance(child, Group):
            raise TypeError("%s is not a group" % child)
        if child in self.children:
            self.children.remove(child)
        if self in child.parents:
            child.parents.remove(self)

    def replace_child(self, oldchild, newchild):
        oldchild.del_parent(self)
        newchild.add_parent(self)

    def add_host(self, host):
        if not isinstance(host, Host):
            raise TypeError("%s is not a host" % host)
        if host not in self.hosts:
            self.hosts.append(host)
        if self not in host.groups:
            host.groups.append(self)

    def del_host(self, host):
        if not isinstance(host, Host):
            raise TypeError("%s is not a host" % host)
        if host in self.hosts:
            self.hosts.remove(host)
        if self in host.groups:
            host.groups.remove(self)

    def reorder_children(self, oldindex, newindex):
        """
        The children are a list, and
        remember the order of inclusion.
        """
        self.children = self.change_element_index(
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
        self.parents = self.change_element_index(
            self.parents,
            oldindex,
            newindex
        )

    def delete(self, reparent_groups=False,
               reparent_hosts=False, reparent_vars=False):
        """
        Wipes a group of the surface of the earth.
        Allow extreme kindness by reparenting data if
        necessary.
        """

        while len(self.hosts) != 0:
            if reparent_hosts:
                for parent in self.parents:
                    self.hosts[0].add_group(parent)
            self.hosts[0].del_group(self)
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

    def has_host(self, hostname):
        return any([True for host in self.hosts if host.name == hostname])

    def has_group(self, groupname):
        return any([True for group in self.children + self.parents if group.name == groupname])

class Host(InventoryObject):

    __slots__ = ['name', 'groups', 'vars', 'priority']

    def __init__(self, name=None):
        if not is_valid_host(name):
            raise Exception("Invalid host name")
        else:
            super(Host, self).__init__(name)
        self.groups = []

    def add_group(self, group):
        group.add_host(self)

    def del_group(self, group):
        group.del_host(self)

    def reorder_groups(self, oldindex, newindex):
        self.groups = self.change_element_index(
            self.groups,
            oldindex,
            newindex
        )

    def delete(self):
        while len(self.groups) != 0:
            group = self.groups[0]
            group.del_host(self)

    def has_group(self, groupname):
        return any([True for group in self.groups if group.name == groupname])


class Inventory(object):
    def __init__(self):
        self.groups = {}
        self.hosts = {}

    def add_special_groups(self):
        self.add_group('ungrouped')
        self.add_group('all')
        self.groups['all'].add_child(self.groups['ungrouped'])

    def load_inventoryjson(self, jsoncontent):
        # _meta is the only information outside group data
        hosts_metadata = jsoncontent.pop('_meta')
        for hostname, hostvars in hosts_metadata['hostvars'].items():
            self.create_host(hostname, hostvars)

        # Groups are created after hosts, so that
        # group/host membership can be updated.
        # group data is structured in json file as
        # groupname: {"children":[], "hosts": [], "vars": {}}
        for groupname, groupinfo in jsoncontent.items():
            # Discover groups and their structure
            self.add_group(groupname, groupinfo)

    # refactor add group
    # to be split into add, create, and update
    def add_group(self, groupname, groupinfo=None, allow_update=True):
        """ This adds a group with groupname.
        By default it allows updating a new group groupname with
        groupinfo. If allow_update=False, only new groups are allowed.
        THe difference is useful for inventory serialization:
        We can recursively add_groups on parents/children, but
        care about their variables later.
        """
        is_new_group = False
        if groupname not in self.groups.keys():
            is_new_group = True
        if is_new_group or allow_update:
            self._process_groupadd(groupname, groupinfo, is_new_group)
        elif groupinfo:
            # The group exists AND the updates are not allowed
            raise ValueError

    def _process_groupadd(self, groupname, groupinfo=None, is_new_group=False):
        try:
            priority = groupinfo.get('priority', 0)
        except AttributeError as e:
            if groupinfo is not None:
                raise Exception("Unknown Exception %s" % e)
            else:
                priority = 0

        if is_new_group:
            self.groups[groupname] = Group(name=groupname)
            # Don't update priority when updating an existing group, unless
            # explicity told so in a separate function
            self.set_group_priority(groupname, priority)

        if groupinfo:
            for subgroup in itertools.chain(
                    groupinfo.get('children', []),
                    groupinfo.get('parents', [])):
                self.add_group(subgroup)

            # Now proceed with hierarchy, merging the new (if any) to the existing.
            for child in groupinfo.get('children', []):
                self.groups[groupname].add_child(self.groups[child])
            for parent in groupinfo.get('parents', []):
                self.groups[groupname].add_parent(self.groups[parent])
            for new_vars in \
                    groupinfo.get('vars', {}), groupinfo.get('group_vars', {}):
                self.groups[groupname].set_vars(new_vars, priority)
            for host in groupinfo.get('hosts',[]):
                self.hosts[host].add_group(self.groups[groupname])

    def del_group(self, groupname, **kwargs):
        if groupname in self.groups:
            grouptodelete = self.groups.pop(groupname)
            grouptodelete.delete(**kwargs)

    def rename_group(self, groupname, newgroupname):
        if groupname in self.groups and newgroupname not in self.groups:
            self.groups[newgroupname] = self.groups.pop(groupname)
            self.groups[newgroupname].name = newgroupname

    def convert_group(self, groupname, newgroupname):
        """
        Convert is not a delete with reparent.
        It's really ensuring a group named newgroupname exists
        and contains the content of the old group named groupname.
        If the newgroupname is an already existing group, then
        a merge should happen, merging the old group groupname into
        newgroupname, merging its vars, children, parents, and hosts.
        Else it's just the creation of a new group that happens.
        """
        groupinfo = dict()
        groupinfo['children'] = [child.name for child in self.groups[groupname].children if child is not self.groups.get(newgroupname, False) ]
        groupinfo['parents'] = [parent.name for parent in self.groups[groupname].parents if parent is not self.groups.get(newgroupname, False)]
        groupinfo['vars'] = self.groups[groupname].vars
        groupinfo['hosts'] = [host.name for host in self.groups[groupname].hosts]
        self.del_group(groupname)
        self.add_group(newgroupname, groupinfo=groupinfo)

    def set_group_priority(self, groupname, priority):
        """ Allows the user to set a priority to a group, for variable
        merging purposes
        """
        if groupname in self.groups:
            self.groups[groupname].priority = priority

    def add_host(self, hostname, hostvars=None, prio=0):
        if hostname in self.hosts:
            self.update_host(hostname, hostvars, prio)
        else:
            self.create_host(hostname, hostvars)

    def create_host(self, hostname, hostvars=None):
        if hostname in self.hosts:
            raise Exception("Host already exists")
        else:
            self.hosts[hostname] = Host(name=hostname)
        if hostvars:
            self.hosts[hostname].set_vars(hostvars, 0)

    # Refactor this to have hostvars and prio optional, to
    # not always override prio
    def update_host(self, hostname, hostvars=None, prio=0):
        """ Update host variables, and priority of a host"""
        try:
            self.hosts[hostname].priority = prio
        except KeyError as exc:
            raise Exception("Host %s does not exist. Traceback: %s" % (hostname,exc))
        if hostvars:
            self.hosts[hostname].set_vars(hostvars, prio)

    def del_host(self, hostname):
        try:
            # No need to pass kwargs, removing host doesn't need
            # reparenting or anything.
            self.hosts[hostname].delete()
            del self.hosts[hostname]
        except KeyError:
            pass

    def rename_host(self, hostname, newhostname):
        if newhostname not in self.hosts:
            self.hosts[newhostname] = self.hosts.pop(hostname)
            self.hosts[newhostname].name = newhostname
        else:
            raise Exception("Host %s already exists" % (newhostname))

    def count_hosts(self):
        return len(self.hosts)

    def count_groups(self):
        """ Counts the amount of user defined groups.
        Doesn't count 'all' and 'ungrouped' special groups.
        """
        return len(self.groups)-2

    def write_output_json(self):
        # Ensure special groups are present
        self.add_special_groups()

        # Prepare output dictionary
        output = dict()
        output[u'_meta'] = {u'hostvars': {}}
        for hostname, hostdata in self.hosts.items():
            # hostdata is the host object, containing variables as
            # a dictionary ready to use
            output[u'_meta'][u'hostvars'][hostname] = hostdata.vars
            # In case of a valid but not standard inventory
            # you might have no "ungrouped" group.
            # So loading that would result in hosts not
            # part of this group, but not part of any other
            # group.
            # For these hosts, make sure they are in ungrouped
            if len(hostdata.groups) == 0:
                hostdata.add_group(self.groups[u'ungrouped'])
            # But also make sure ungrouped is not still present
            # if additional groups were added
            else:
                hostdata.del_group(self.groups[u'ungrouped'])
        # Now output group mapping
        # Keep as value only ['children','vars', 'hosts']
        # of each group
        for groupname, groupdata in self.groups.items():
            output.update({groupname: {}})
            kids = [ child.name for child in groupdata.children]
            if kids:
                output[groupname].update({u'children': kids})
            machines = [host.name for host in groupdata.hosts]
            if machines:
                output[groupname].update({u'hosts': machines})
            if groupdata.vars:
                output[groupname].update({u'vars': groupdata.vars})
            print(output)
        return output
