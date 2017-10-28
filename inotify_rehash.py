#!/bin/env python3
import os
import threading
import pyinotify
import configparser
import argparse
import pydle

# Global variable we use to access pydle.
global client

# Get the config file from our command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument("--config", required = True)
args = parser.parse_args()

# Parse the config file.
config = configparser.ConfigParser()
config.read(args.config)

# Get all the variables.
file = config.get("main", "file")
username = config.get("main", "username")
password = config.get("main", "password")
server = config.get("main", "server")
nick = config.get("main", "nickname")
port = config.getint("main", "port")
ssl = config.getboolean("main", "ssl")

# Define our pydle client here.
class pydle_client(pydle.Client):
	""" Subclass of pydle.Client to OPER-up on connect. """
	def on_connect(self):
		""" Called on connect. """
		# Call superclass.
		super().on_connect()

		# OPER-up.
		self.rawmsg("OPER", username, password)

	def on_raw_491(self, message):
		""" Called when we get numeric 491 'Invalid oper credentials'. """
		# Failed to OPER-up, exit.
		print("ERROR: We have failed to OPER-up, exiting.")

		# Kill the main thread.
		os._exit(1)

# Threading function to run pydle in a seperate thread.
def start_pydle():
	# We need to access our global.
	global client

	# Setup pydle from the variables defined from the top of the file.
	client = pydle_client(nick)
	client.connect(server, port, ssl)
	client.handle_forever()

# Setup the pydle thread.
pydle_thread = threading.Thread(target=start_pydle, daemon = True)
pydle_thread.start()

# Setup inotify.
wm = pyinotify.WatchManager()

# Only watch for a modification of the file.
mask = pyinotify.IN_MODIFY

# EventHandler for pyinotify.
class EventHandler(pyinotify.ProcessEvent):
	def process_IN_MODIFY(self, event):
		# Run a REHASH when the file is modified.
		global client
		client.rawmsg("REHASH")

# Setup the EventHandler and Notifier.
handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

# Setup the watch.
wdd = wm.add_watch(file, mask)

# Loop forever.
notifier.loop()
