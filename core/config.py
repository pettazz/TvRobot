"""
This contains all the main app settings
"""

TVROBOT = {
	'log_path': 'logs',
	'completed_move_method': 'FABRIC'
}

TRANSMISSION = {
	'server': '192.168.1.103',
	'port': 9091,
	'user': 'osto',
	'password': 'lol',
	'SSH': {
		'port': 200,
		'user': 'osto',
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
	'server': '192.168.1.106',
	'port': 3306,
	'user': 'tvrobot',
	'password': 'lol', 
	'schema': 'TvRobot'
}

MEDIA = {
	'server': '192.168.1.108',
	'port': 201,
	'user': 'osto',
	'password': 'lol',
	'remote_path': {
		'Movie': '/home/osto/Ext/Movies',
		'TVShow': '/home/osto/Ext/Tv.Shows'
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