import itertools
import copy

def mergedicts(dict1, dict2, prios=(0,0)):
    """
    Merges a and b together.
    In case of ties, prios determine who's the winner
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
                # If one of the values is not a dict, you can't continue merging it.
                # Take the one who has the higher prio.
                elif prios[0] < prios[1]:
                    yield (k, dict2[k])
                else:
                    yield (k, dict1[k])
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])
    

class Inventory(object):
    def __init__(self):
        self.groups = {}
        self.hosts = {}
        
    def load_inventoryjson(self, jsoncontent):
        # _meta is the only information outside group data
        hosts_metadata = jsoncontent.pop('_meta')
        for hostname, hostvars in hosts_metadata['hostvars'].items():
            self.add_host(hostname, hostvars)

        # group data is structured in json file as groupname: {"children":[], "hosts": []}
        for groupname, groupinfo in jsoncontent.items():
            # Discover groups and their structure
            self.add_group(groupname, groupinfo)
        
    def add_group(self, groupname, groupinfo=None, allow_update=True):
        """ Add group will be called with an update or not update
        mode, depending on the situation, to add a group to the
        inventory
        """
        is_new_group=False
        if groupname not in self.groups.keys():
            is_new_group=True
        if is_new_group or allow_update:
            self._process_groupadd(groupname, groupinfo, is_new_group)
        elif groupinfo:
            # The group exists AND the updates are not allowed
            raise KeyError

    def _process_groupadd(self, groupname, groupinfo=None, is_new_group=False):
        for subgroup in itertools.chain(groupinfo.get('children',[]), groupinfo.get('parents',[])):
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
        for parent in groupinfo.get('parents',[]):
            self.groups[groupname].add_parent(self.groups[parent])
        for new_vars in groupinfo.get('vars',{}), groupinfo.get('groupvars',{}):
            result = mergedicts(self.groups[groupname].groupvars,
                                new_vars,
                                prio=(self.groups[groupname].priority,
                                      priority
                                )
            )
            self.groups[groupname].groupvars = dict(result)
            

    def del_group(self, groupname):
        pass

    def rename_group(self, groupname, newgroupname):
        pass
            
    def set_group_priority(self, groupname, priority):
        """ Allows the user to set a priority to a group, for variable
        merging purposes
        """
        self.groups[groupname].priority = priority

    
    def add_host(self):
        pass

class Group(object):
    def __init__(self, groupname='', groupvars=None, children=None, parents=None, hosts=None, priority=0):
        self.groupname = groupname
        self.groupvars = groupvars if groupvars is not None else {}
        self.children = children if children is not None else []
        # Parents is not an ansible information, but it's useful for
        # global loop avoidance when deleting/renaming things.
        self.parents = parents if parents is not None else []
        self.hosts = hosts if hosts is not None else []
        # For VARIABLE precedence resolving, we introduce a priority.
        self.priority = priority
    def __repr__(self):
        return "Group(groupname='%s')"%(self.groupname)
    def add_parent(self, parent):
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
        oldparent.del_child(self)
        newparent.add_child(self)
    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)
        if self not in child.parents:
            child.parents.append(self)
    def del_child(self, child):
        if child in self.children:
            self.children.remove(child)
        if self in child.parents:
            child.parents.remove(self)
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
    def change_element_index(listname, oldindex, newindex):
        """
        The children and parents are a list, and
        remember the order of inclusion.
        This method is used to modify the order,
        by changing an item from its old position
        to a new position, keeping the rest of the
        list intact. This is useful for altering the
        group variable flattening: the flattening is done by
        browsing the lists. (Last match wins if tie)
        """
        if listname == 'parents':
            self.parents.insert(newindex,self.parents.pop(oldindex))
        elif listname == 'children':
            self.children.insert(newindex,self.children.pop(oldindex))

    def delete(self):
        for child in self.children:
            child.del_parent(self)
        for parent in self.parents:
            parent.del_child(self)
        for host in self.hosts:
            host.del_group(self)
    # def __del__(self):
    #     print("Deleting myself")


class Host(object):
    def __init__(self, hostname='', hostvars=None, groups=None):
        self.hostname = hostname
        self.hostvars = hostvars if hostvars is not None else {}
        self.groups = []
        if groups is not None:
            for group in groups:
                self.add_group(group)
    def __repr__(self):
        return "Host(hostname='%s')" % (self.hostname)
    def add_group(self, group):
        group.add_host(self)
    def del_group(self, group):
        group.del_host(self)