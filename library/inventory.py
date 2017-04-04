#!/usr/bin/python
import MySQLdb
from ansible.module_utils.basic import *

class database_connect:
    def __init__(self,hostname,username,password,database):
        self.hostname=hostname
        self.username=username
        self.password=password
        self.database=database

    def getConnect(self):
        self.db = MySQLdb.connect(self.hostname,self.username,self.password,self.database)
        return self.db

    def getCursor(self):
        self.cursor = self.db.cursor()
        return self.cursor

    def query(self,queryType,sql):
        try:
            if queryType is "SELECT":
                self.cursor.execute(sql)
                return self.cursor.fetchall()
            elif queryType is "INSERT" or queryType is "UPDATE" or queryType is "DELETE":
                self.cursor.execute(sql)
                self.db.commit()
                return None
        except:
                self.db.rollback()
                return "ERROR"

def main():
    module = AnsibleModule(
        argument_spec=dict(
        database=dict(
        hostname=dict(required=True),
        name=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),type="dict"),
        ipAddress=dict(required=True),
        group=dict(required=True)
        )
    )

    if module.params["database"]:
        database = module.params["database"]
        db = database_connect(hostname=database['hostname'],username=database['username'],password=database['password'],database=database['name'])
        db.getConnect()
        db.getCursor()
        if module.params['ipAddress'] and module.params['group']:
            response = db.query("INSERT","INSERT INTO hosts(hosts,group_name) values(\'{0}\',\'{1}\')".format(module.params['ipAddress'],module.params['group']))
            if response is not "ERROR":
                module.exit_json(changed=True,meta={'message': "IP Address {0} is added to group {1}".format(module.params['ipAddress'],module.params['group'])})
            elif response is "ERROR":
                module.fail_json(changed=True, msg={'message':"failed to added {0}".format(response)})

if __name__ == "__main__":
    main()
