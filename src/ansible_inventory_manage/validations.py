def is_valid_name(name=None):
    if name and isinstance(name, str):
        return True
    else:
        return False


def is_valid_host(name=None):
    if is_valid_name(name) and \
       len(name) < 253 and \
       name.replace('_', '').replace('-', '').replace('.','').isalnum():
        return True
    else:
        return False