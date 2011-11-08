from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

import core.config as config

env.hosts = [config.TRANSMISSION['SSH']['user'] + '@' + \
             config.TRANSMISSION['server'] + ':' + \
             str(config.TRANSMISSION['SSH']['port'])]

def move_video(local_path = None, remote_path = None):
    local_path = shellquote(local_path)
    remote_path = shellquote(remote_path)

    run('scp -P %s %s %s@%s:%s' % 
        (config.MEDIA['port'],
        local_path,
        config.MEDIA['user'],
        config.MEDIA['server'],
        remote_path))

def shellquote(s):
    return "'" + s.replace("'", "'\\''") + "'"