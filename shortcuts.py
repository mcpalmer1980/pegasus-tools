import pylnk3, os, sys
from fuzzywuzzy import process as fuzz
from PyInquirer import prompt

home = os.path.expanduser('~') + '/'

link_path = home + 'Games/_shortcuts/d_games/'
game_prefix = len('C:/Games/')
check_prefix = home + 'Games/'

screenshots = os.listdir(home + 'Games/media/coverart')
banners = os.listdir(home + 'Games/media/banners')

def main():
	data, missing = get_data(ask("Filter broken links"))
	matches, unmatched = get_matches(data)
	fixed, unmatched = select_each(unmatched)
	save_metadata(matches, fixed)
	save_log(missing, unmatched)


def get_data(_filter=True):
	links = [ link_path + f for f in os.listdir(link_path) if f.endswith('.lnk') ]
	print('found {} shortcuts in {}'.format(len(links), link_path))

	data = []
	missing = []
	for l in links:
		name, command, found = get_link_path(l)
		if found or not _filter:
			shot, score = fuzz.extractOne(name, screenshots)
			banner, _ = fuzz.extractOne(name, banners)
			data.append((name, command, score, shot, banner))
		else:
			missing.append((name, command))
	print('good = {}, broken = {}'.format(len(data), len(missing)))
	return sorted(data, key=lambda x: x[0].lower()), missing


def get_matches(data):
	matches = []
	missing = []
	for item in data:
		name, command, score, shot, banner = item
		if score > 88:
			matches.append(item)
		else:
			missing.append(item)
	return matches, missing


def get_link_path(f, repl=None ):
	try:
		link = pylnk3.Lnk(f)
	except:
		return '', '', None

	command = link.link_info.path[game_prefix:].replace('\\', '/')
	path, binary = os.path.split(command)
	work = link.work_dir
	name = os.path.basename(f)[:-4]

	found = True if os.path.exists(check_prefix + command) else False
	return name, './' + command, found


def select_each(missing):
	good = []
	bad = []
	skip = False
	for item in missing:
		name, command, score, shot, banner = item
		result = fuzz.extract(name, screenshots, limit=3)
		question = dict(
			type = "rawlist",
			name = 'which',
			message = '{} - ({}%)'.format(name, score),
			choices = [i[0] for i in result] + ['None', 'Cancel'])

		if not skip:
			result = prompt(question)['which']

		if result == 'Cancel':
			bad.append(item)
			skip = True
		elif result == 'None' or skip:
			bad.append(item)
		else:
			print(result)
			good.append((name, command, score, shot, banner))
	return good, bad


def save_metadata(matches, fixed):
	metadata = (
		"collection: Windows Games\n"
		"shortname: windows\n"
		"launch: '{file.path}'\n\n")

	for name, command, score, shot, banner in matches + fixed:
		metadata += (
			"game: {}\n"
			"file: {}\n"
			"assets.screenshot: ./media/{}\n"
			"assets.banner: .media/{}\n\n").format(name, command, shot, banner)
	result = ask('Save metadata?', (
				'Yes, megadata.pegasus.txt',
				'Yes, specify',
				'No, just print'))
	if 'specify' in result:
		outfile = get_string('filename')
	elif 'Yes' in result:
		outfile = 'metadata.pegasus.txt'
	else:
		print(metadata)
		return
	with open(outfile, 'w') as f:
		f.write(metadata)


def save_log(missing, unmatched):
	log = (
		"#############\n"
		"MISSING MEDIA\n"
		"#############\n"
		"{} items\n".format(len(unmatched)))
	for name, command, score, shot, banner in unmatched:
		log += '{} -> "{}"\n'.format(name, command)
	

	log += (
		"\n\n############\n"
		"BROKEN LINKS\n"
		"############\n"
		"{} items\n".format(len(missing)))
	for name, command in missing:
		log += '{} -> "{}"\n'.format(name, command)
	if ask('Save missing.txt file?'):
		with open('missing.txt', 'w') as f:
			f.write(log)
	print(log)


def ask(message, choices=None):
	if choices:
		question = [dict(
			type = 'list',
			message = message,
			choices = choices,
			name = 'result',
			default = True)]
	else:
		question = [dict(
			type = 'confirm',
			message = message,
			name = 'result',
			default = True)]
	return prompt(question)['result']

def get_string(message):
	question = [dict(
        type ='input',
        name = 'result',
        message = message)]
	return prompt(question)['result']

if __name__ == '__main__':
	main()