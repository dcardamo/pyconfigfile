#!/bin/bash
# this is a comment.  Anything after the # is a comment to the end
# the line.  This is also now a multiline comment
TEST=1   # variable TEST equals 1 now.
TEST=2;  # same thing, but shows how semicolons are allowed
TEST1=1; TEST2=2  # more than one thing allowed
TEST2=$TEST  # $TEST designates a previous variable.
list=(item1 item2 $TEST)  # this creates a list
list[2]=$TEST     # sets an item in the list
LENGTH=${#list}   # gets the length of the list
OUTPUT=`ps -ef | grep init` # OUTPUT gets command output
echo "Something"  # when parsed, this will be printed.
