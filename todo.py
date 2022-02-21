import yaml
import os
import string
import random

from pprint import pprint

with open("config.yaml", "r") as file:
	config = yaml.safe_load(file)


db_path = 'task.yaml'
closed_path = 'closed.yaml'
default_task = {'task1': [{'multi': False,
						   'users': 902988020876193803,
						   'description': "",
						   'estimated_time': 120,
						   'real_time': 78}]}


def get_db(path=db_path):
	"""
	Get data from the db
	:return: yaml with all data
	"""
	if not os.path.isfile(path):
		with open(path, "w+") as f:
			yaml.safe_dump(default_task, f)
	with open(path, 'r') as f:
		return yaml.safe_load(f)


def write_db(data, closed=0):
	"""
	Write the new data to the DB
	:param data:
	:return:
	"""
	if closed == 0:
		with open(db_path, "w+") as f:
			yaml.safe_dump(data, f)
	else:
		with open(closed_path, "w+") as f:
			yaml.safe_dump(data, f)


def new_id():
	db = get_db()
	ids = [task for task in db]
	n = 0
	while 1:
		if n == 100:
			return
		id = str()
		for i in range(0, 4):
			id += random.choice(string.ascii_uppercase)
		if id not in ids:
			return id
		n += 1


def add(user_id: int, description: str):
	"""
	Add a new task to the DB
	:param user_id: ID of the user creating the task
	:param description: task content
	:return: ID of the new task or -1
	"""
	pprint(description)
	db = get_db()
	task_id = new_id()
	new = {task_id: {
		'users': [user_id],
		'description': description,
		'real_time': 0,
		'tags': []}}
	db.update(new)
	write_db(db)
	return task_id


def edit(task_id, key, value):
	"""
	Edit a task
	:param task_id:
	:param data:
	:return:
	"""
	db = get_db()
	for task in db:
		if task == task_id:
			db[task][key] = value
			write_db(db)
			return 1
	return 0


def close(task_id):
	"""
	Close a task
	:param task_id: ID of the task
	:return: 1 if worked 0 else
	"""
	try:
		db = get_db()
		closed = get_db(closed_path)
		task = get_task(task_id)
		if task_id not in db:
			return 0
		db.pop(task_id)
		write_db(db)
		closed.update(task)
		write_db(closed, 1)
	except ValueError as e:
		return 0, e
	return 1


def get_task(task_id):
	"""
	Get data for a specific task
	:param task_id: ID of the task
	:return: data of the task
	"""
	db = get_db()
	for task in db:
		if task == task_id:
			return {task: db[task]}
	return {}


def get_value(task_id, key):
	"""
	Get the value for a given key in a given task
	:param task_id: ID of the task
	:param key: key to search (users, tags, description...)
	:return: the searched value
	"""
	try:
		task = get_task(task_id)
		id = list(task.keys())[0]
		return task[id][key]
	except ValueError as e:
		return e


def get_tasks_user(user_id):
	"""
	Get all task for a specific user
	:param user_id: ID of the user
	:return: data of the task
	"""
	res = list()
	db = get_db()
	for task in db:
		if int(user_id) in db[task]['users']:
			res.append({task: db[task]})
	return res


def add_tag(task_id, tag):
	"""
	Add a tag to a task
	:param task_id: ID of the task
	:param tag: tag to add
	"""
	task = get_task(task_id)
	tags = task[task_id]['tags']
	tags.append(tag)
	if edit(task_id, "tags", tags):
		return 1
	return 0


def assign(task_id, user_id):
	"""
	Assign a task to a user
	:param task_id:
	:param user_id:
	:return:
	"""
	ids = get_value(task_id, 'users')
	tags = get_value(task_id, 'tags')
	if user_id not in ids:
		if 'Multi' in tags:
			if not len(ids):
				edit(task_id, 'tags', 'Multi')
			ids.append(user_id)
			edit(task_id, 'users', ids)
		else:
			return 0
	return 1


def unassign(task_id, user_id):
	"""
	Unassigned a task
	:param task_id: ID of the task
	:param user_id: user ID to remove
	"""
	ids = get_value(task_id, 'users')
	tags = get_value(task_id, 'tags')
	if user_id in ids:
		ids.remove(user_id)
		if not ids and 'Multi' not in tags:
			add_tag(task_id, 'Multi')
		edit(task_id, 'users', ids)
		return 1
	return 0


def get_unassigned():
	"""
	Get all unassigned tasks
	"""
	res = list()
	db = get_db()
	for task in db:
		if not len(db[task]['users']):
			res.append({task: db[task]})
	return res

