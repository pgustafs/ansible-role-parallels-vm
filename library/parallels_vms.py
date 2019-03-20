#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Peter Gustafsson
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: parallels_vms
short_description: Module to manage Virtual Machines in Parallels Desktop
description:
   - This module manages whole lifecycle of the Virtual Machine(VM) in Parallels Desktop.
author: Peter Gustafsson
version_added: "0.1"
options:
   name:
        description:
            - Name of the Virtual Machine to manage.
   state:
        description:
            - Should the Virtual Machine be present/absent/running/stopped/paused.
            - I(present) state will create/update VM and don't change its state if it already exists.
            - I(running) state will create/update VM and start it.
            - I(absent) state deletes the VM.
            - I(stopped) state will stop the VM.
            - I(paused) state will pause the VM.
        choices: [ resent, absent, running, stopped, paused ]
        default: present
   clone:
        description:
            - If I(yes) then the disks of the created virtual machine will be cloned and independent of the template.
            - This parameter is used only when C(state) is I(running) or I(present) and VM didn't exist before.
        type: bool
        default: 'no'
   template:
        description:
            - Name of the template, which should be used to create Virtual Machine.
            - Required if cloning VM.
   memory:
        description:
            - Amount of memory in MB of the Virtual Machine. (for example 1024, 2048).
   cpu_count:
        description:
            - Set the number of virtual CPUs allocated to this Virtual Machine.
notes:
   - Requires The Parallels Virtualization SDK for Mac
'''

EXAMPLES = '''
- name: Creates a new Virtual Machine from template named 'rhel7_template'
  parallels_vms:
    state: running
    name: myvm
    clone: True
    template: rhel7_template
    memory: 2048
    cpu_count: 2

- name: Remove VM, if VM is running it will be stopped
  parallels_vms:
    state: absent
    name: myvm
'''
from ansible.module_utils.basic import AnsibleModule
import json
import logging
import sys
# Import the main Parallels Python API package.
import prlsdkapi
# Define constants for easy referencing of the Parallels Python API modules.
consts = prlsdkapi.prlsdk.consts
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def login_server(server, security_level):
    try:
        # The call returns a prlsdkapi.Result object on success.
        result = server.login_local('', 0, security_level).wait()
    except prlsdkapi.PrlSDKError as err:
        return False, err
    return True, result


def search_vm(server, vm_to_find):
    try:
        result = server.get_vm_list().wait()
    except prlsdkapi.PrlSDKError, e:
        print "Error: %s" % e
        return
    for i in range(result.get_params_count()):
        vm = result.get_param_by_index(i)
        vm_config = vm.get_config()
        vm_name = vm_config.get_name()
        if vm_name == vm_to_find:
            return vm


def edit_vm(server, name, data):
    memory = data['memory']
    cpu_count = data['cpu_count']
    vm = search_vm(server, name)
    # Begin the virtual machine editing operation.
    try:
        vm.begin_edit().wait()
    except prlsdkapi.PrlSDKError, err:
        return False, err
    # Obtain the VmConfig object containing the virtual machine
    # configuration information.
    vm_config = vm.get_config()
    if memory:
        if memory != vm_config.get_ram_size():
            vm.set_ram_size(int(memory))
    if cpu_count:
        if cpu_count != vm_config.get_cpu_count():
            vm.set_cpu_count(int(cpu_count))
    # Commit the changes.
    try:
        vm.commit().wait()
    except prlsdkapi.PrlSDKError, err:
        return False, err
    return True, {"status": "VM CHANGED"}


def create_vm(server, name):
    a = "b"
    return False, {"status": "NOT IMPLEMENTED, USE CLONE"}


def clone_vm(server, name, template):
    # Get the prlsdkapi.Vm object for the template
    template = search_vm(server, template)
    # If template exist clone a new vm from it
    if template:
        try:
            template.clone(name, "", False).wait()
        except prlsdkapi.PrlSDKError, err:
            return False, err
        return True, {"status": "SUCCESS"}
    return False, {"status": "TEMPLATE DOES NOT EXIST"}


def start_vm(server, name):
    vm = search_vm(server, name)
    # Start the virtual machine.
    if vm:
        try:
            vm.start().wait()
        except prlsdkapi.PrlSDKError, err:
            return False, err
        return True, {"status": "SUCCESS"}
    return False, {"status": "TEMPLATE DOES NOT EXIST"}


def stop_vm(server, name):
    vm = search_vm(server, name)
    # Stop the virtual machine.
    if vm:
        try:
            vm.stop().wait()
        except prlsdkapi.PrlSDKError, err:
            return False, err
        return True, {"status": "SUCCESS"}
    return False, {"status": "VM DOES NOT EXIST"}


def delete_vm(server, name):
    vm = search_vm(server, name)
    # delete the virtual machine.
    if vm:
        try:
            vm.delete().wait()
        except prlsdkapi.PrlSDKError, err:
            return False, err
        return True, {"status": "SUCCESS"}
    return False, {"status": "VM DOES NOT EXIST"}


def create(server, data):
    state = data['state']
    name = data['name']
    template = data['template']
    clone = data['clone']
    memory = data['memory']
    cpu_count = data['cpu_count']
    vm = search_vm(server, name)
    if vm:
        # vm already exist, exit
        return False, False, {"status": "VM EXIST"}
    if clone:
        # clone vm from template
        success, response = clone_vm(server, name, template)
        if not success:
            return True, False, response
    else:
        success, response = create_vm(server, name)
        if not success:
            return True, False, response
    if memory or cpu_count:
        success, response = edit_vm(server, name, data)
        if not success:
            return True, False, response
    if state == "running":
        success, response = start_vm(server, name)
        if not success:
            return True, False, response
    return False, True, response


def delete(server, data):
    name = data['name']
    vm = search_vm(server, name)
    if vm:
        stop_vm(server, name)
        success, response = delete_vm(server, name)
        if success:
            return False, True, response
        else:
            return True, False, response
    return False, False, {"status": "VM DOES NOT EXIST"}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str'),
            clone=dict(type='bool', default=False),
            template=dict(type='str'),
            memory=dict(type='str'),
            cpu_count=dict(type='str'),
            state=dict(
                default='present',
                choices=['present', 'absent', 'running', 'stopped', 'paused']),
        ),
        supports_check_mode=True,
        required_if=(
            ['state', 'present', ['name']],
            ['state', 'absent', ['name']],
            ['clone', 'true', ['template']]
        )
    )
    # Initialize the library for Parallels Desktop.
    prlsdkapi.init_desktop_sdk()

    # Create a Server object and log in to Parallels Desktop.
    server = prlsdkapi.Server()
    login_server(server, consts.PSL_NORMAL_SECURITY)

    choice_map = {
        "present": create,
        "absent": delete,
        "running": create,
        "stopped": create,
        "paused": create,
    }

    is_error, has_changed, result = choice_map.get(
        module.params['state'])(server, module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error", meta=result)


if __name__ == '__main__':
    main()
