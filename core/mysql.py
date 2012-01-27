"""

Wrapper for MySQL functions to make life easier

"""

import MySQLdb
import time
import core.config as config

class DatabaseManager():
    """This class wraps database fucntions for us for easy use.  It connects to the database"""

    def __init__(self, conf_creds=None):
        """
        Gets database information from conf.py and creates a connection.
        """
        retry_count = 3
        backoff = 10
        count = 0
        while count < retry_count:
            try:
                self.conn = MySQLdb.connect(host=config.DATABASE['server'],
                    user=config.DATABASE['user'],
                    passwd=config.DATABASE['password'],
                    db=config.DATABASE['schema'])
                self.conn.autocommit(True)
                self.cursor = self.conn.cursor()
                return
            except:
                time.sleep(backoff)
                count = count + 1
        if retry_count == 3:
            raise Exception("Unable to connect to MySQL Database after three retries.")

    def fetchall_query_and_close(self,query,values):
        """Executes a query, gets all the values and then closes up the connection"""
        self.cursor.execute(query, self.__sanitize(values))
        retval = self.cursor.fetchall()
        self.__close_db()
        return retval

    def fetchone_query_and_close(self,query,values):
        """Executes a query, gets the first value and then closes up the connection"""
        self.cursor.execute(query, self.__sanitize(values))
        retval = self.cursor.fetchone()
        self.__close_db()
        return retval

    def execute_query_and_close(self, query, values):
        """Executes a query and closes the connection"""
        retval = self.cursor.execute(query, self.__sanitize(values))
        self.__close_db()
        return retval

    def __sanitize(self, values):
        retval = {}
        for key in values:
            if type(values[key]) == str:
                value = self.conn.escape_string(values[key])
            else:
                value = values[key]
            retval[key] = value
        return retval

    def __close_db(self):
        self.cursor.close()
        self.conn.close()
