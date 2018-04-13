from ansible_inventory_manage.names import Name, Hostname, Groupname, Varname


class TestNames(object):

    def test_valid_names(self):
        assert Name.is_valid_name('a')
        assert not Name.is_valid_name()
        
    def test_valid_hostnames(self):
        assert Hostname.is_valid_name('a')
        assert not Hostname.is_valid_name('_')
        assert not Hostname.is_valid_name('-')
        assert Hostname.is_valid_name('a-')
        assert Hostname.is_valid_name('a-a')
        assert not Hostname.is_valid_name('a-$a')
        assert Hostname.is_valid_name('-a')
        assert not Hostname.is_valid_name()

    def test_valid_groupnames(self):
        assert Groupname.is_valid_name('a')
        assert not Groupname.is_valid_name()
