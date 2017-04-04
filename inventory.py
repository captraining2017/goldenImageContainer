#!/usr/bin/env python

'''
Example custom dynamic inventory script for Ansible, in Python.
'''

import os
import sys
import argparse
from database import *
try:
    import json
except ImportError:
    import simplejson as json

class Inventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()
        self.db=database_connect(hostname="localhost",username="root", password="knoppixUser@",database="inventory")

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.internal_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.internal_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.internal_inventory()

        print json.dumps(self.inventory);

    # Example inventory for testing.
    def internal_inventory(self):
        response = self.db.query("SELECT","select hosts, group_name from hosts")
        group={}
        for application in response:
            if not group.has_key(application[1]):
                group[application[1]]={"hosts":[application[0]],"vars":{}}
            else:
                (group[application[1]]["hosts"]).append(application[0])
        var = self.db.query("SELECT","select * from group_vars")
        for key in var:
            if key[0] in group:
                group[key[0]]['vars']['ansible_ssh_user'] = key[1]
                group[key[0]]['vars']['ansible_ssh_private_key_file'] = key[2]
        return group
    # Empty inventory for testing.
    def empty_inventory(self):
        response = self.db.query("SELECT", "SELECT hosts, group_name FROM hosts")
        group={}
        for group in response:
            if not group.has_key(group[1]):
                group[group[1]]={'hosts':[group[0]],'vars':{}}
            else:
                (group[group[1]]['hosts']).append(group[0])
        var = self.db.query("SELECT","select * from group_vars")
        for key in var:
            if key[0] in group:
                group[key[0]]['vars']['ansible_ssh_user'] = key[1]
                group[key[0]]['vars']['ansible_ssh_private_key_file'] = key[2]
        return group

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

# Get the inventory.
Inventory()
