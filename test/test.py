#!/usr/bin/env python2
import sys


sys.path[0] = ".."
from ConfigFile import *

# Start of test code:
print "Performing tests..."
print "Testing Shell Mode..."

try:
	shell = ConfigFile("config.sh")
except SyntaxError.ExecNotAllowed:
	print "\tExecution Checking(disallowed)...ok"
else:
	print "\tExecution Checking(disallowed)...failed"


try:
	shell = ConfigFile("config.sh", allowExec=1)
except SyntaxError.ExecNotAllowed:
	print "\tExecution Checking(allowed)...failed"		
else:
	print "\tExecution Checking(allowed)...ok"


print "Dump:"
print "-" * 30
for key in shell.keys():
	print "%s=%s" %(key, shell[key])
