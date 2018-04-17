import ansible_inventory_manage.validations as validate


class TestNames(object):

    def test_valid_names(self):
        assert validate.is_valid_name('a')
        assert not validate.is_valid_name()

    def test_valid_hostnames(self):
        assert validate.is_valid_host('a')
        assert not validate.is_valid_host('_')
        assert not validate.is_valid_host('-')
        assert not validate.is_valid_host('(')
        assert validate.is_valid_host('a-')
        assert validate.is_valid_host('a-a')
        assert not validate.is_valid_host('a-$a')
        assert validate.is_valid_host('-a')
        assert not validate.is_valid_host()
        assert validate.is_valid_host('9')
        assert validate.is_valid_host('9')
        assert validate.is_valid_host('9')

    def test_valid_groupnames(self):
        assert validate.is_valid_name('a')
        assert not validate.is_valid_name()
