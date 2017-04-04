import MySQLdb
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
            self.getConnect()
            self.getCursor()
            if queryType is "SELECT":
                self.cursor.execute(sql)
                return self.cursor.fetchall()
            elif queryType is "INSERT" or queryType is "UPDATE" or queryType is "DELETE":
                self.cursor.execute(sql)
                self.db.commit()
        except:
                self.db.rollback()
                return "ERROR"
