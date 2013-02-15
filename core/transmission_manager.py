import transmissionrpc
from config import TRANSMISSION

import core.strings as strings
from core.mysql import DatabaseManager
from core.util import Util

class TransmissionManager:
    def __init__(self):
        #try to connect to the Transmission server
        self.daemon = transmissionrpc.Client(
            address=TRANSMISSION['server'], 
            port=TRANSMISSION['port'], 
            user=TRANSMISSION['user'], 
            password=TRANSMISSION['password'])

    def __getattr__(self, name):
        return getattr(self.daemon, name)

    def reindex_torrents(self):
        print strings.TRANSMISSION_REINDEXING_START
        torrents = TransmissionManager().list()
        print torrents
        for torrent in torrents:
            download_name_hash = self.util.md5_string(torrent.name) 
            query = """
                SELECT guid FROM Download WHERE
                download_name_hash = '%(download_name_hash)s'
            """
            result = DatabaseManager().fetchone_query_and_close(query, {'download_name_hash': download_name_hash})
            if result is not None:
                guid = result[0]
                new_id = torrent.id
                print strings.TRANSMISSION_REINDEXING_TORRENT % (guid, new_id)
                query = """
                    UPDATE Download SET transmission_id = %(new_id)s
                    WHERE guid = '%(guid)s'
                """
                DatabaseManager().execute_query_and_close(query, {'guid': guid})
            else:
                print strings.UNRECOGNIZED_TORRENT % torrent.id

        print strings.TRANSMISSION_REINDEXING_FINISH