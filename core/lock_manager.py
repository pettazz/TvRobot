import time
import uuid

from mysql import DatabaseManager
from user_manager import UserManager

class LockManager:


    def is_locked(self, lock_type):
        now = int(time.time())
        query = """
            SELECT guid FROM TaskLock WHERE
            type = %(lock_type)s AND
            time_unlocked = 0
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'lock_type': lock_type, 'now': now})
        return result is not None
    
    def set_lock(self, lock_type, user_id=None):
        if self.is_locked(lock_type):
            raise Exception("Could not set %s lock, already locked." % lock_type)
        guid = uuid.uuid4()
        now = int(time.time())
        if user_id is None:
            user_id = UserManager().get_user_id()
        query = """
            INSERT INTO TaskLock
            (guid, type, User, time_locked)
            VALUES 
            (%(guid)s, %(lock_type)s, %(userid)s, %(now)s)
        """
        result = DatabaseManager().execute_query_and_close(query, {'guid': guid, 'lock_type': lock_type, 'userid': user_id, 'now': now})
        if result:
            return guid
        else:
            raise Exception("Could not set %s lock." % lock_type)
    
    def unlock(self, lock_guid=None, user_id=None, lock_type=None):
        now = int(time.time())
        if lock_guid is None:
            if user_id is None:
                user_id = UserManager().get_user_id()
            if lock_type is None:
                query = """
                    UPDATE TaskLock 
                    SET time_unlocked = %(now)s
                    WHERE
                    User = %(user_id)s AND 
                    time_unlocked = 0
                """
                result = DatabaseManager().execute_query_and_close(query, {'now': now, 'user_id': user_id})
            else:
                query = """
                    UPDATE TaskLock 
                    SET time_unlocked = %(now)s
                    WHERE
                    lock_type = %(lock_type)s AND
                    User = %(user_id)s AND 
                    time_unlocked = 0
                """
                result = DatabaseManager().execute_query_and_close(query, {'lock_type': lock_type, 'now': now, 'user_id': user_id})
        else:
            query = """
                UPDATE TaskLock 
                SET time_unlocked = %(now)s
                WHERE
                guid = %(lock_guid)s
                LIMIT 1
            """
            result = DatabaseManager().execute_query_and_close(query, {'lock_guid': lock_guid, 'now': now})
        return result