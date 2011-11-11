from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

import core.config as config

env.hosts = [config.TRANSMISSION['SSH']['user'] + '@' + \
             config.TRANSMISSION['server'] + ':' + \
             str(config.TRANSMISSION['SSH']['port'])]

def move_video(local_path, remote_path):
    local_path = __shellquote(local_path)
    remote_path = __shellquote(remote_path)

    run('scp -P %s %s %s@%s:%s' % 
        (config.MEDIA['port'],
        local_path,
        config.MEDIA['user'],
        config.MEDIA['server'],
        remote_path))

def unrar_file(rar_path, save_path):
    rar_path = __shellquote(rar_path)
    save_path = __shellquote(save_path)

    run('mkdir %s' % save_path)
    run('unrar e %s %s' % (rar_path, save_path))

def delete_file(guid_path):
    guid = __shellquotes(guid_path)

    run('rm -r %s' % guid_path)

def __shellquote(s):
    return s.replace(' ', '\ ')