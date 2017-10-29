#!/bin/env python3
import os
import signal
import pyinotify
import configparser
import argparse

# Subclass configparser.RawConfigPaser to add getlist().
class config(configparser.RawConfigParser):
	def getlist(self, section, option):
		""" Gets a list from a CSV value. """
		# Get the csv from the config.
		value = self.get(section, option)

		# Create the returning list.
		return_object = list()

		# If the value is blank the return a blank list.
		if value == "" or not value:
			return return_object

		# Convert CSV to a list.
		for each in value.split(','):
			# Strip the trailing space if any.
			each = each.strip(' ')
			# Add it to the list
			return_object.append(each)

		# Return the list.
		return return_object

# Get the config file and pid from our command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument("--config", required = True)
parser.add_argument("--pid", required = True, type = int)
args = parser.parse_args()

# Parse the config file.
config = config()
config.read(args.config)

# Get the files to scan.
files = config.getlist("main", "files")

# Setup inotify.
wm = pyinotify.WatchManager()

# Only watch for a modification of the file.
mask = pyinotify.IN_MODIFY

# EventHandler for pyinotify.
class EventHandler(pyinotify.ProcessEvent):
	def process_IN_MODIFY(self, event):
		# Run a REHASH (send SIGHUP) when the file is modified.
		try:
			os.kill(args.pid, signal.SIGHUP)
		except ProcessLookupError:
			print("Error sending signal to inspircd, is it running?")
			os._exit(1)

# Setup the EventHandler and Notifier.
handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

# Setup the watches.
wdd = []
for file in files:
	wdd.append(wm.add_watch(file, mask))

# Loop forever.
notifier.loop()
