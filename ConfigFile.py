#!/usr/bin/env python
# -*- mode: python; tab-width: 4 -*-
# vim: set tabstop=4 shiftwidth=4 expandtab:

# Copyright (C) Ottawa Python Author's Group
# Website: http://www.opag.ca
# Mailing list:  opag@opag.ca
# Authors: Dan Cardamore <dan@hld.ca>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import os
import re

DEBUG = 0               # turn debug printing off by default

# define some constants.  These can't change.
# this class is used to enforce constants in python.
class const:
    class ConstError(TypeError): pass
	def __setattr__(self,name,value):
        if self.__dict__.has_key(name):
            raise self.ConstError, "Can't rebind const(%s)"%name
        self.__dict__[name]=value

const.TRUE=1
const.CHECK=1
const.NOCHECK=0
const.FALSE=0

# Our Exception classes
class ConfigFileSyntaxError:
	"""Raised when there is an error in the syntax of the config file itself"""
	SyntaxError = "Error parsing the file because of improper syntax"
	NonExistantKey = "The key requested does not exist"
	UnknownType = "The first line of the file was not descriptive enough"
	ExecNotAllowed = "You do not have access to execute commands"

class ConfigFileUsageError:
	"""Raised when this module is used incorrectly"""
	pass

class IncompleteFunctionality:
	"""For incomplete code"""
	pass

class ConfigFile:
	"""Abstract class which will use another to perform the actual work
	of parsing a file.  This class will determine which file type the
	Config file is, and then instantiate that handler."""

	def __init__(self, file, allowExec=const.FALSE, whitespace=const.NOCHECK, ro=const.TRUE):
		"""default constructor where by default execution is turned
		off, and so is whitespace checking.  These can be overriden
		by the actual ConfigFile parsers"""
		self.allowExec = allowExec
		self.whitespace = whitespace
		self.readonly = ro
		self.fileFormat = None

		#determine what time of config format the file is in:
		type = open(file, "r").readline()
		
		format = re.compile("#!.*(bash|tcsh|csh|sh)")  # match shell mode
		if format.search(type):
			self.fileFormat = "shell"
			self.config = ConfigFileShell(file, allowExec=self.allowExec,
										  whitespace=self.whitespace, ro=self.readonly)

		format = re.compile("^#!.*python") # python format
		if not self.fileFormat and format.search(type):
			self.fileFormat = "python"
			self.config = ConfigFilePython(file, allowExec=self.allowExec,
										  whitespace=self.whitespace, ro=self.readonly)


		format = re.compile("\[.*\]")  # ConfigParser format
		if not self.fileFormat and format.search(type):
			self.fileFormat = "ConfigParser"
			raise IncompleteFunctionality, "We don't handle ConfigParser yet"

		if not self.fileFormat:
			raise ConfigFileSyntaxError.UnknownType

	def format(self):
		return self.fileFormat

	def __setitem__(self, key, value):
		"""Called when writing to the file"""
		if self.readonly:
			raise ConfigFileUsageError, "Attempted to write while file readonly"
		self.config[key] = value


	def __getitem__(self, key):
		"""Called to read a value out of the config file.  It will already be cached"""
		return self.config[key]
		

	def keys(self):
		return self.config.keys()



class ConfigFileGeneric:
	"""Base class for all configuration file classes"""
	def __init__(self, file, allowExec=const.FALSE, whitespace=const.NOCHECK, ro=const.TRUE):
		self.allowExec = allowExec
		self.whitespace = whitespace
		self.readonly = ro
		self.fileFormat = None
		self.config = {}

		if self.readonly:
			self.file = open(file, "r")
		else:
			self.file = open(file, "r+")

	def __getitem__(self, key):
		if not exists(self.config[key]):
			raise NonExistantKey, key		
		return self.config[key]

	def __setitem__(self, key, value):
		raise IncompleteFunctionality, "This format does not support writing"

	def keys(self):
		return self.config.keys()


class ConfigFileShell(ConfigFileGeneric):
	"""Handles Shell format configuration files"""
	def __init__(self, file, allowExec=const.FALSE, whitespace=const.NOCHECK, ro=const.TRUE):
		ConfigFileGeneric.__init__(self, file, allowExec=allowExec, whitespace=whitespace, ro=ro)
		self.fileFormat = "shell"
		self.parse()

	def parse(self):
		for line in self.file.readlines():
			line = line[:-1]   # remove newline character
			line = re.sub(" #.*", "", line) # ignore anything following a ' #'
			line = re.sub("^#.*", "", line) # ignore any line starting with a '#'
			line = re.sub("^\s+", "", line) # remove leading whitespace
			if line == "":
				if DEBUG: print "---Empty Line Found---"
				continue

			key = re.search("^\w+", line).group(0)  # first word is the key
			if DEBUG: print "---Key: %s---" %key
			if key == None:
				raise ConfigFileSyntaxError.SyntaxError, "variable name not found"

			if re.search("\`", line):       # is this a command?
				if not self.allowExec:
					raise ConfigFileSyntaxError.ExecNotAllowed, line

				command = re.search("\`.*\`", line).group(0)
				command = command[:-1]    # remove the last back tick
				command = command[1:]     # remove the first back tick
				#subsitute the command for a string
				output = ""
				for outline in os.popen(command, 'r').readlines():
					output = output + outline[:-1]
				output = output                # put it into a list
				line = re.sub("\`.*\`", "\"" + output + "\"", line)
				print line
			
			arrayItems = re.search("\(.*\)", line)			
			if arrayItems:           # are we starting a list?
				if DEBUG: print "---Starting a list!---"
				continue
			elif re.search("\[", line):         # are we working with an item of a list?
				if DEBUG: print "---Modifying a value in a list---"
				continue

			if DEBUG: print line         # debug
		

class ConfigFilePython(ConfigFileGeneric):
	"""Handles Python format configuration files"""
	def __init__(self, file, allowExec=const.FALSE, whitespace=const.NOCHECK, ro=const.TRUE):
		ConfigFileGeneric.__init__(self, file, allowExec=None, whitespace=None, ro=const.TRUE)
		self.fileFormat = "python"
		self.parse()

	def parse(self):
		for line in self.file.readlines():
			line = line[:-1]   # remove newline character
			print line



# Start of test code:
if __name__ == "__main__":
	print "Performing tests..."
	print "Testing Shell Mode..."
	DEBUG = 0
	try:
		shell = ConfigFile("tests/config.sh")
	except ConfigFileSyntaxError.ExecNotAllowed:
		print "\tExecution Checking(disallowed)...ok"
	else:
		print "\tExecution Checking(disallowed)...failed"
	try:
		shell = ConfigFile("tests/config.sh", allowExec=1)
	except ConfigFileSyntaxError.ExecNotAllowed:
		print "\tExecution Checking(allowed)...failed"		
	else:
		print "\tExecution Checking(allowed)...ok"
	


## 	print "Testing Python Mode..."
## 	python = ConfigFile("tests/config.py")
