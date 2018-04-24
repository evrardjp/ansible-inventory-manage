import re

def parse_ruleset(filename):
    with open(filename, 'r') as rulefile:
        rules = fd.readlines(rulefile.read())

def parseline(keywords):
    """
    Converts a series of keywords into actions
    """
    action_map = {
        'add group': 'add_group',
        'edit group': 'rename_group'
        'drop group': 'del_group'
    }
    keywords[0:1]