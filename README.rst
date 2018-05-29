This is a library to manipulate Ansible Inventories.

It's independent of ansible by design, so that it doesn't need to track
ansible code and is version independent.

It only relies on what ansible expects as inventories (the json structure),
which hasn't changed for a long time now.

A standard inventory json is like this:

    ```
    {
        _meta:{
            hostvars:{
                <hostname>:{
                    var1: value1
                }
            }
        },
        all:{
            children: [],
            vars:{
                var2: value2
            },
        },
        groupname1:{
            children:[],
            hosts:[],
        }
        groupname2:{
            children:[],
            vars:{
                var3: value3
            },
        }
    }
    ```

This lib allows the loading of multiple jsons into memory, and manipulate the
inventory objects, and vars precedence.

Usage will explained in documentation soon.

You can submit patches with git-review and gerrithub (``pip install git-review``)

  # git clone https://review.gerrithub.io/evrardjp/ansible-inventory-manage
  # git review -s
  # git checkout -b my_super_patch
  # git review -f

