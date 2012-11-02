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
                raise Exception("User does not exist.")

        return user_id

    def get_user_phone_by_id(self, id):
        query = """
            SELECT phone FROM User WHERE
            id = %(id)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'id': id})
        if result is not None:
            return result[0]
        else:
            return None

    def get_user_id_by_phone(self, phone):
        if phone.startswith('+1'):
            phone = phone[2:]
        query = """
            SELECT id FROM User WHERE
            phone = %(phone)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'phone': phone})
        if result is not None:
            return result[0]
        else:
            return None