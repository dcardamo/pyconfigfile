#!/usr/bin/env python2
# -*- mode: python; tab-width: 4 -*-
# vim: set tabstop=4 shiftwidth=4 expandtab:

# Copyright (C) Dan Cardamore
# Website: http://www.hld.ca/opensource/CVSWEB/pyConfigFile
# Mailing list:  opag@opag.ca Ottawa Python Authors Group
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
class SyntaxError:
	"""Raised when there is an error in the syntax of the config file itself"""
	Unknown = "Error parsing the file because of improper syntax"
	NonExistantKey = "The key requested does not exist"
	UnknownType = "The first line of the file was not descriptive enough"
	ExecNotAllowed = "You do not have access to execute commands"

class UsageError:
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
			raise SyntaxError.UnknownType

	def format(self):
		return self.fileFormat

	def __setitem__(self, key, value):
		"""Called when writing to the file"""
		if self.readonly:
			raise UsageError, "Attempted to write while file readonly"
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
		if not self.config.has_key(key):
			raise SyntaxError.NonExistantKey, key		
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
		configlines = self.file.readlines()
		while (configlines):
			line = configlines[0]         # get the first line
			configlines = configlines[1:] # remove the line from the list
			value = ""
			line = line[:-1]   # remove newline character
			line = re.sub(" #.*", "", line) # ignore anything following a ' #'
			line = re.sub("^#.*", "", line) # ignore line starting with a '#'
			line = re.sub("^\s+", "", line) # remove leading whitespace
			line = re.split("\;", line)  # split the line for all ';'
			configlines = line + configlines
			line = configlines[0]                 # get the first line
			configlines = configlines[1:]
			
			if line == "":
				if DEBUG: print "---Empty Line Found---"
				continue

			# check for config command first
			firstword = re.search("\w+", line).group(0)
			if firstword == "echo":
				print line
				continue

			# grab the key
			key = re.search("^\w+", line).group(0)  # first word is the key
			if DEBUG: print "---Key: %s---" %key
			if key == None:
				raise SyntaxError.Unknown, "variable name not found"
			line = re.search("\=(.*)", line).group(0) # remove the key
			line = line[1:] # remove the '='

			# is this a system command?
			if re.search("\`.*\`", line):
				if not self.allowExec:
					raise SyntaxError.ExecNotAllowed, line

				command = re.search("\`.*\`", line).group(0)
				command = command[1:-1]   # remove the back ticks
                #subsitute the command for a string
				output = ""
				for outline in os.popen(command, 'r').readlines():
					output = output + outline[:-1]
				line = re.sub("\`.*\`", "\"" + output + "\"", line)


			# perform substitution
			varbs = re.search("\$\w+", line)
			if varbs:
				count = 0
				while (1):
					try:
						testkey = varbs.group(count)[1:]
					except IndexError:
						break
					if not self.config.has_key(testkey):
						raise SyntaxError.NonExistantKey, "%s does not exist" %testkey
					line = re.sub(re.escape(varbs.group(count)),
								  self.config[testkey], line)
					count = count + 1


			# are we starting a list?
			arrayItems = re.search("\(.*\)", line)
			if arrayItems:
				if DEBUG: print "---Starting a list!---"
				continue
			elif re.search("\[", line):         # working with a list item
				if DEBUG: print "---Modifying a value in a list---"
				continue
			else:  # working with a plain variable
				if DEBUG: print "---Creating a variable---"
				value = line

			self.config[key] = value

			#set the item
			self.config[key] = value

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


