import discord
import yaml
import asyncio
from datetime import datetime

import todo
from pprint import pprint
from discord.ext import commands, tasks

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("debug.log", "a")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

with open("config.yaml", "r") as file:
	config = yaml.safe_load(file)

with open("msg.yaml", "r") as file:
	msg = yaml.safe_load(file)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['bot_symbol'], intents=intents, help_command=None)
bot.remove_command('help')

##############################################################################
# Events
##############################################################################


@bot.event
async def on_ready():
	guild = discord.utils.get(bot.guilds, name=config["discord_guild"])
	logger.debug(f'{datetime.now()} {bot.user} is connected to the guild: {guild.name} (id: {guild.id})')
	await bot.change_presence(activity=discord.Game(name="$help"))


##############################################################################
# Commands
##############################################################################


@bot.command(name='help')
async def help(ctx, cmd=""):
	if not cmd:
		desc = ""
		for m in msg:
			if 'desc' in m:
				desc += "**" + m.replace('desc_', '') + "**: " + msg[m] + "\n"
		desc += "\n*Tape `$help <commande>` pour avoir plus d'infos sur une commande*.\n*Ex:* `$help add`"
		embed = discord.Embed(title="HELP", description=desc, color=config['color'])
		await ctx.send(embed=embed)
		return

	try:
		desc = msg["usage_" + cmd]
		embed = discord.Embed(title="HELP pour la commande " + cmd, description=desc, color=config['color'])
		await ctx.send(embed=embed)
		return
	except:
		embed = discord.Embed(title="ERROR", description="Cette commande n'existe pas.", color=config['color'])
		await ctx.send(embed=embed)


@bot.command(name='add')
async def add(ctx, *args):
	"""
	Create a new task.
	:param ctx: discord context
	:param minutes: estimated time in minutes to finish the task
	:param description: content of the task
	"""
	try:
		minutes = int(args[0])
		description = " ".join(args[1:])
	except:
		embed = discord.Embed(title="ERROR", description=msg['usage_add'], color=config['color'])
		await ctx.send(embed=embed)
		return


	# Add the task to the DB
	task_id = todo.add(ctx.author.id, minutes, description)
	if task_id == -1:
		await ctx.send(msg['fail_add'])
		return

	# Create and send the add task message
	tags = msg['tags']
	desc = msg['success_add'].format(task_id, description)
	i = 0
	for tag in tags:
		desc += list(tag.keys())[0] + " " + list(tag.values())[0]
		desc += '\n' if i % 5 == 0 else "  |  "
		i += 1
	desc = "".join(desc.rsplit(" | ", 1))
	embed = discord.Embed(title="SUCCESS", description=desc, color=config['color'])
	message = await ctx.send(embed=embed)

	# Add reactions to the message
	for tag in tags:
		await message.add_reaction(list(tag.values())[0])

	# Verify the reaction and add the corresponding tag to the task
	def check(reaction, user):
		if not user == ctx.author:
			return 0
		for tag in tags:
			if str(reaction.emoji) == list(tag.values())[0]:
				todo.add_tag(task_id, list(tag.keys())[0])
		return 0

	# Wait for user reactions to the message
	try:
		await bot.wait_for('reaction_add', timeout=300.0, check=check)
	except asyncio.TimeoutError:
		return


@bot.command(name='close')
async def close(ctx, task_id, real_time):
	try:
		real_time = int(real_time)
		if real_time <= 0:
			await ctx.send("Commence pas a essayer de baiser le game")
			return
	except:
		embed = discord.Embed(title="ERROR", description=msg['fail_close1'], color=config['color'])
		await ctx.send(embed=embed)
		return

	task = todo.get_task(task_id)
	if task and todo.close(task_id):
		id = list(task.keys())[0]
		desc = msg['success_close'].format(task_id, task[id]['description'], str(real_time))
		embed = discord.Embed(title="Tâche terminée !", description=desc, color=config['color'])
		await ctx.send(embed=embed)
	else:
		embed = discord.Embed(title="Oups", description="Pas de tâche a ce nom ou erreur", color=config['color'])
		await ctx.send(embed=embed)
	return


@bot.command(name='tasks')
async def tasks(ctx, *args):
	if not len(args):
		tasks = todo.get_tasks_user(ctx.author.id)
		desc = task_to_message(tasks)
		embed = discord.Embed(title="Liste de tes tâches", description=desc, color=config['color'])
		await ctx.send(embed=embed)
	else:
		try:
			user = int(args[0])
		except:
			await ctx.send(msg['fail_tasks1'])
			return
		tasks = todo.get_tasks_user(user)
		user = bot.get_user(user)
		desc = task_to_message(tasks)
		embed = discord.Embed(title="Liste des tâches de " + user.name, description=desc, color=config['color'])
		await ctx.send(embed=embed)
	return


@bot.command(name='unassigned')
async def unassigned(ctx):
	tasks = todo.get_unassigned()
	if len(tasks):
		desc = task_to_message(tasks)
		embed = discord.Embed(title="Liste des tâches non assignées", description=desc, color=config['color'])
		await ctx.send(embed=embed)
	else:
		await ctx.send("Aucune tâche non assignée.")
	return


@bot.command(name='unassign')
async def unassign(ctx, task_id):
	if todo.unassign(task_id, ctx.author.id):
		desc = msg['success_unassign'].format(task_id, todo.get_value(task_id, 'description'))
		embed = discord.Embed(title="SUCCESS", description=desc, color=config['color'])
		await ctx.send(embed=embed)
	else:
		embed = discord.Embed(title="ERROR", description="Tâche introuvable.", color=config['color'])
		await ctx.send(embed=embed)


@bot.command(name='assign')
async def assign(ctx, task_id):
	if todo.assign(task_id, ctx.author.id):
		desc = msg['success_assign'].format(task_id, todo.get_value(task_id, 'description'))
		embed = discord.Embed(title="SUCCESS", description=desc, color=config['color'])
		await ctx.send(embed=embed)
	else:
		embed = discord.Embed(title="ERROR", description="Tâche introuvable.", color=config['color'])
		await ctx.send(embed=embed)



@bot.command(name='info')
async def info(ctx, task_id):
	task = todo.get_task(task_id)
	desc = ""
	for t in task:
		desc += "**" + t "**\n**Description**"
	embed = discord.Embed(title="Info task " + task_id, description=task, color=config['color'])
	await ctx.send(embed=embed)
	return


##############################################################################
# Other functions
##############################################################################

def task_to_message(tasks):
	desc = msg['task_exemple']
	if len(tasks):
		for task in tasks:
			id = list(task.keys())[0]
			desc += msg['task_template'].format(id, todo.get_value(id, 'description'))
		return desc
	else:
		return


bot.run(config['discord_token'])