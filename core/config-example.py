"""
This contains all the main app settings
"""

TVROBOT = {
	'log_path': 'logs',
	'completed_move_method': 'FABRIC'
}

TRANSMISSION = {
	'server': 'mytransmissionserver.org',
	'port': 9091,
	'user': 'lol',
	'password': 'hunter2',
	'SSH': {
		'port': 22,
		'user': 'shamwow',
	}
}

SELENIUM = {
	'server': 'localhost',
	'port': '4444',
	'timeout': 30,
	'log_path': 'logs'
}

DATABASE = {
	'type': 'mysql',
	'server': 'mymysqlserver.xxx',
	'port': 3306,
	'user': 'tvrobot',
	'password': 'hunter2', 
	'schema': 'TvRobot'
}

MEDIA = {
	'server': 'myplexmediaserver.com',
	'port': 2020, #this is SSH btw
	'user': 'slapchop',
	'password': 'hunter2',
	'remote_path': {
		'Movie': '/home/slapchop/Movies',
		'Set': '/home/slapchop/Movies',
		'Episode': '/home/slapchop/Ext/Tv Shows',
		'Season': '/home/slapchop/Tv Shows',
		'Set': '/home/slapchop/Tv Shows',
	}
}

#lists of filetypes we'll allow
FILETYPES = {
	"video": (
		'mkv', 'avi', 'mp4', 'm2ts', 'm2s'
	),
	"compressed": (
		'zip', 'rar'
	)
}