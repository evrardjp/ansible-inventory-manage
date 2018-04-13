class Name(object):
    def __init__(self, name):
        self.name = name if self.is_valid_name(name) else None

    def __repr__(self):
        return self.name

    @staticmethod
    def is_valid_name(name=None):
        return False if not name else True


class Hostname(Name):
    @classmethod
    def is_valid_name(cls, name=None):
        if not super(cls, cls).is_valid_name(name):
            return False
        if len(name) > 253:
            return False
        if name.replace('_', '').replace('-', '').isalnum():
            return True
        return False


class Groupname(Name):
    pass


class Varname(Name):
    pass