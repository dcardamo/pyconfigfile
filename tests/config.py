#!/usr/bin/python

# this is a comment.  Anything after the # is a comment to the end
# the line.  This is also now a multiline comment
test=1   # variable TEST equals 1 now.
test = "test";  # same thing, but shows how semicolons are allowed
test1=1; test2=2  # more than one thing allowed
test2=test  # TEST designates a previous variable.
list=["item1", 2,
	  test)  # this creates a list.  Tab's are used.
list[1]=test     # sets an item in the list
length=len(list)   # gets the length of the list
dict={'key':'value',
	  'key2':list}
dict['key2'] = 2
output = command('ps -ef | grep bash')
print "Something"  # when parsed, this will be printed.
