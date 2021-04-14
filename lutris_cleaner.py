#!/bin/python3
'''
This is a simple python script that can clean your Lutris game libary
It will search for broken entries whose binary/executable have been removed
It will remove broken entries if permission is granted

by Michael C Palmer
'''
import os, sqlite3
from distutils.spawn import find_executable

data_file = os.path.expanduser('~') + '/.local/share/lutris/pga.db'
banner_path = os.path.expanduser('~') + '/.local/share/lutris/banners/'
art_path = os.path.expanduser('~') + '/.local/share/lutris/coverart/'
configs = os.path.expanduser('~') + '/.config/lutris/games/'


def main():
	'''
	search for games with missing binaries and display them to the user
	clean the broken entries if users grants permission
	'''

	db = load_db(data_file)
	missing = get_missing(db)
	if len(missing) > 0 and get_permission(missing):
		remove_missing(missing, db)
	else:
		print('everything looks clean to me')

	print('bye')


def load_db(data_file):
	'''
	load the lutris database
	'''
	if not os.path.exists(data_file):
		print('lutris db not found at {}'.format(data_file))
		return

	else:
		print('opening lutris db at {}'.format(data_file))
		db = sqlite3.connect(data_file)
		try:
			curs = db.execute('SELECT id, name, slug, directory from games')
			print('db looks valid')
			return db
		except:
			print('sqlite db is not a lutris game database')


def get_missing(db):
	'''
	scan the database for items whose executable is missing
	'''
	missing = []
	curs = db.execute('SELECT id, name, runner, configpath from games')

	for id, name, runner, configpath in curs:
		path = get_yaml_exe(configs + configpath)
		if path:
			if runner == 'wine':
				if not os.path.exists(path):
					missing.append( (id, name, configpath) )
			
			elif runner == 'linux':
				if not find_executable(path):
					missing.append( (id, name, configpath) )
		else:
			missing.append( (id, name, configpath) )
	return missing


def get_permission(missing):
	'''
	print missing item list and ask user if the items should be removed
	'''

	print('The following Lutris games are missing binaries')
	for id, name, configpath in missing:
		print('  ' + name)
	
	result = input('Would you like to remove these items(y/N)?')
	if result.lower() in ('y', 'yes'):
		return True


def remove_missing(missing, db):
	'''
	remove database entry, yml file, and artwork for games whose binary is missing
	'''
	for id, name, configpath in missing:
		db.execute('DELETE from games where id="{}"'.format(id))
		remove_art(name)
		config = configs + configpath + '.yml'
		if os.path.exists(config):
			os.remove(config)
			print('removed ' + config)
		
	db.commit()
	print('{} items removed'.format(len(missing)))


def remove_art(name):
	'''
	remove the artwork for a missing game
	will find png and jpg files (lower case extension only)
	'''
	for ext in ('.jpg', '.png'):
		banner = banner_path + name + ext
		art = art_path + name + ext
		if os.path.exists(banner):
			os.remove(banner)
		if os.path.exists(art):
			os.remove(art)


def get_yaml_exe(config):
	'''
	simple function that retrieves the game->exe parameter from a yml file
	included to avoid using a module outside the standard library
	'''
	indent = None
	path = ''
	if not os.path.exists(config + '.yml'):
		return
	with open(config + '.yml') as lines:
		for line in lines:
			if line.strip().startswith('exe: '):
				indent = len(line) - len(line.lstrip())
				path = line.strip()[4:].strip()
			elif indent:
				if indent < len(line) - len(line.lstrip()):
					path = path + ' ' + line.strip()
				else:
					return path


if __name__ == '__main__':
	print(__doc__)
	main()
