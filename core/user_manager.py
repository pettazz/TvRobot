import getpass

from mysql import DatabaseManager


class UserManager:


    def get_user_id(self):
        user_name = getpass.getuser()
        query = """
            SELECT id FROM User WHERE
            username = %(user_name)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'user_name': user_name})
        if result is not None:
            user_id = result[0]
        else:
            user_name = raw_input("TvRobot Username: ")
            query = """
                SELECT id FROM User WHERE
                username = %(user_name)s
            """
            result = DatabaseManager().fetchone_query_and_close(query, {'user_name': user_name})
            if result is not None:
                user_id = result[0]
            else:
                raise("User does not exist.")

        return user_id