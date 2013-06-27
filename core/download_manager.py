import subprocess
import shutil
import os
import uuid

import core.strings as strings
import core.config as config
from core.util import Util
from core.mysql import DatabaseManager
from core.transmission_manager import TransmissionManager

class DownloadManager:
    """ Provides methods for interacting with Downloads, mainly finding files and
        moving them around """

    def __init__(self):
        self.util = Util()

    def get_video_file_path(self, files):
        max_size = 0
        file_id = None
        decompress = False
        for torrent_id in files:
            print strings.FINDING_VIDEO_FILE % torrent_id
            for f in files[torrent_id]:
                if "sample" not in files[torrent_id][f]['name'].lower() \
                    and "trailer" not in files[torrent_id][f]['name'].lower() \
                    and "bonus features" not in files[torrent_id][f]['name'].lower():
                    ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                    if ext in config.FILETYPES['video'] and files[torrent_id][f]['size'] > max_size:
                        decompress = False
                        max_size = files[torrent_id][f]['size']
                        file_name = files[torrent_id][f]['name']
                    elif ext in config.FILETYPES['compressed'] and files[torrent_id][f]['size'] > max_size:
                        if ext == 'zip':
                            decompress = 'zip'
                            max_size = files[torrent_id][f]['size']
                            file_name = files[torrent_id][f]['name']
                        elif ext == 'rar':
                            decompress = 'rar'
                            max_size = files[torrent_id][f]['size']
                            file_name = files[torrent_id][f]['name']
                        else:
                            return None
        if decompress:
            if decompress == 'rar':
                file_name = self.unrar_file(file_name)
            if decompress == 'zip':
                file_name = self.unzip_file(file_name)

            file_dir = os.path.join(TransmissionManager().get_session().download_dir, file_name.rsplit('/*', 1)[0])
            files_list = [f for f in os.listdir(file_dir) if (os.path.isfile(os.path.join(file_dir, f)) and f.lower().rsplit('.', 1)[1] in config.FILETYPES['video']) ]
            if not files_list:
                raise FakeDownloadException()
        elif file_name:
            if file_name.lower().rsplit('.', 1)[1] not in config.FILETYPES['video']:
                raise FakeDownloadException()
        else:
            return None
        
        return file_name

    def get_all_video_file_paths(self, files, kill_samples = True):
        videos = []
        for torrent_id in files:
            print strings.FINDING_VIDEO_FILE % torrent_id
            for f in files[torrent_id]:
                ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                if ext in config.FILETYPES['video'] and (files[torrent_id][f]['selected']):
                    videos.append(files[torrent_id][f]['name'])
                elif ext in config.FILETYPES['compressed'] and (files[torrent_id][f]['selected']):
                    if ext == 'rar':
                        done = self.unrar_file(files[torrent_id][f]['name'])
                        videos.append(files[torrent_id][f]['name'])
                    elif ext == 'zip':
                        done = self.unzip_file(files[torrent_id][f]['name'])
                        videos.append(files[torrent_id][f]['name'])
                    else:
                        raise Exception(strings.UNSUPPORTED_FILE_TYPE % files[torrent_id])
        if kill_samples:
            videos = self.__filter_samples(videos)
        videos = self.__filter_video_only(videos)
        if len(videos) > 0:
            return videos
        else:
            raise FakeDownloadException()

    def __filter_samples(self, file_list):
        return [f for f in file_list if "sample" not in f.lower() and "trailer" not in f.lower()]

    def __filter_video_only(self, file_list):
        return [f for f in file_list if f.lower().rsplit('.', 1)[1] in config.FILETYPES['video']]

    def unrar_file(self, file_path):
        print strings.UNRAR
        guid = str(uuid.uuid4().hex)
        src_path = self.util.shellquote("%s/%s" % (TransmissionManager().get_session().download_dir, file_path))
        dest_path = self.util.shellquote("%s/%s/" % (TransmissionManager().get_session().download_dir, guid))
        try:
            if config.TVROBOT['completed_move_method'] == 'FABRIC':
                subprocess.check_call("fab unrar_file:rar_path='%s',save_path='%s'" % (src_path, dest_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            elif config.TVROBOT['completed_move_method'] == 'LOCAL':
                subprocess.check_call("mkdir %s; unrar e %s %s" % (dest_path, src_path, dest_path),
                    stdout=open("%s/log_localfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_localfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            else:
                print "FIX YER CONF. I ONLY KNOW FABRIC AND LOCAL."
        except Exception, e:
            print strings.CAUGHT_EXCEPTION
            raise e

        return "%s/*" % guid

    def unzip_file(self, file_path):
        print strings.UNZIP
        guid = str(uuid.uuid4().hex)
        src_path = self.util.shellquote("%s/%s" % (TransmissionManager().get_session().download_dir, file_path))
        dest_path = self.util.shellquote("%s/%s/" % (TransmissionManager().get_session().download_dir, guid))
        try:
            if config.TVROBOT['completed_move_method'] == 'FABRIC':
                subprocess.check_call("fab unzip_file:zip_path='%s',save_path='%s'" % (src_path, dest_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            elif config.TVROBOT['completed_move_method'] == 'LOCAL':
                subprocess.check_call("mkdir %s; unzip %s -d %s" % (dest_path, src_path, dest_path),
                    stdout=open("%s/log_localfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_localfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            else:
                print "FIX YER CONF. I ONLY KNOW FABRIC AND LOCAL."
        except Exception, e:
            print strings.CAUGHT_EXCEPTION
            raise e

        return "%s/*" % guid

    def delete_video_file(self, file_path):
        file_path = self.util.shellquote(file_path)
        try:
            if config.TVROBOT['completed_move_method'] == 'FABRIC':
                #this isnt a check_call because a lot can go wrong here and its not mission critical
                subprocess.call("fab delete_file:remote_path=\"%s\"" % (file_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            elif config.TVROBOT['completed_move_method'] == 'LOCAL':
                shutil.rmtree(file_path, True)
            else:
                print "FIX YER CONF. I ONLY KNOW FABRIC AND LOCAL."
        except Exception, e:
            print strings.CAUGHT_EXCEPTION
            raise e

    def move_video_file(self, file_path, file_type, showname=None):
        video_name = file_path.rsplit('/', 1)[1]
        if showname:
            remote_path = "%s/%s" % (config.MEDIA['remote_path'][file_type], showname)
            cmd = "fab verify_dir:path=\"%s\"" % (self.util.shellquote(remote_path))
            subprocess.check_call(cmd,
                stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                shell=True)
        else:
            remote_path = config.MEDIA['remote_path'][file_type]
        try:
            if config.TVROBOT['completed_move_method'] == 'FABRIC':
                cmd = "fab move_video:local_path=\"%s\",remote_path=\"%s\"" % (self.util.shellquote(file_path), self.util.shellquote(remote_path))
                subprocess.check_call(cmd,
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            elif config.TVROBOT['completed_move_method'] == 'LOCAL':
                if file_path.endswith('*'):
                    path = file_path.split('*')[0]
                    for f in os.listdir(path):
                        if f.rsplit('.', 1)[1] in config.FILETYPES['video']:
                            m_file = "%s%s" % (path, f)
                            print "copying %s file: %s" % (f.rsplit('.', 1)[1], f)
                            shutil.copy(m_file, remote_path)
                        else:
                            print "skipping %s file: %s" % (f.rsplit('.', 1)[1], f)
                else:
                    shutil.copy(file_path, remote_path)
            else:
                print "FIX YER CONF. I ONLY KNOW FABRIC AND LOCAL."
        except Exception, e:
            print strings.CAUGHT_EXCEPTION
            raise e

    def get_schedule_data(self, transmission_guid):
        query = """
            SELECT E.* FROM EpisodeSchedule E, Download D WHERE
            D.transmission_guid = %(transmission_guid)s AND E.guid = D.EpisodeSchedule
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'transmission_guid': transmission_guid})
        return result

    def get_torrent_type(self, transmission_guid):
        query = """
            SELECT type FROM Download WHERE
            transmission_guid = %(transmission_guid)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'transmission_guid': transmission_guid})
        if result is not None:
            result = result[0]
        return result


class FakeDownloadException(Exception):
    def __init__(self):
        message = "Fake Download detected."
        Exception.__init__(self, message)