Role Name
=========

A brief description of the role goes here.

Requirements
------------

The Parallels Virtualization SDK for Mac
http://www.parallels.com/download/pvsdk/

Role Variables
--------------

A description of the settable variables for this role should go here, including any variables that are in defaults/main.yml, vars/main.yml, and any variables that can/should be set via parameters to the role. Any variables that are read from other roles and/or the global scope (ie. hostvars, group vars, etc.) should be mentioned here as well.


Example Playbook
----------------
### Create vm playbook
```
- hosts: localhost
  vars:
    parallels_vm_name: myawesomevm
    parallels_vm_memory: 512
    parallels_vm_cpu_count: 1
    parallels_vm_state: running
    parallels_vm_clone: True
    parallels_vm_template: "RHEL7.5_template"

  roles:
    - ansible-role-parallels-vm
```
### Delete vm playbook
```
- hosts: localhost
  vars:
    parallels_vm_name: myawesomevm
    parallels_vm_state: absent

  roles:
    - ansible-role-parallels-vm
```
