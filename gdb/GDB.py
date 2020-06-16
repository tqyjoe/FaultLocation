#!/usr/bin/env python
# $Id: GDB.py,v 1.48 2004/06/21 14:03:32 zeller Exp $
# Simple GDB interface

# Copyright (C) 2004 Saarland University, Germany.
# Written by Andreas Zeller <zeller@askigor.org>.
# 
# This file is part of AskIgor.
# 
# AskIgor is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# AskIgor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with AskIgor -- see the file COPYING.
# If not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
# AskIgor is an experimental automated debugging server.
# For details, see the AskIgor World-Wide-Web page, 
# `http://www.askigor.org/',
# or send a mail to the AskIgor developers <info@askigor.org>.

import sys, os
import string
import time
import popen2
import re
import signal
import os
import traceback
import AlarmHandler

from sh_quote import sh_quote


class Error(Exception):
	"""Base class for exceptions in this module."""
	def __init__(self):
		pass

class EOFError(Error):
	"""EOF during GDB command"""
	def __init__(self):
		pass

class TimeOutError(Error):
	"""TimeOut during GDB command"""
	def __init__(self, timeout):
		self.reply = timeout
	def __str__(self):
		return "TimeOut after " + `self.reply` + " seconds"

class NoSymbolsError(Error):
	"""No symbol table found"""
	def __init__(self, reply):
		self.reply = reply
	def __str__(self):
		return `self.reply`

class NotInvokedError(Error):
	"""Debuggee was not invoked"""
	def __init__(self, output):
		self.output = output
	def __str__(self):
		return `self.output`

class UnsupportedLanguageError(Error):
	"""Language not supported"""
	def __init__(self, language):
		self.language = language
	def __str__(self):
		return "Language " + `self.output` + " not supported"


# GDB interface
class GDB:
	prompt = "(gdb)\n";
	issued_pid_magic = "IsSuEd_ThE_pId";
	logging = 0
	language = "c"
	
	fetch_debuggee_pid = 1
	
	signal_timeout     = 5
	cleanup_timeout    = 10
	invocation_timeout = 10
	set_break_timeout  = 10

	def __init__(self, debuggee = ""):
		try:
			if self.child is not None:
				# Already initialized
				return
		except:
			pass

		self.__debuggee = debuggee
		self.__invocation = None
		self.child = None
		self.original_program = None
		self.proxy_child = None

		self.all_functions_cache = None
		self.all_sources_cache = None
		self.all_functions_with_debug_info_cache = None

		self.interactive_functions = {}
		self.verbose = 1

		self.restart()

	def restart(self):
		if self.child is not None:
			del self.child

		self.call()
		self.debuggee_pid = None
		self.__reply_so_far = ""
		self.disabled_functions = {}

		quoted_prompt = string.replace(self.prompt, "\n", "\\n")
		self.__write("set prompt " + quoted_prompt)

		blurb = self.__read_until_prompt()
		self.__initial_messages = blurb.replace("(gdb) ", "", 1)

		if self.language == "c++":
			demangling = "on"
		else:
			demangling = "off"
		
		self.question("set editing off")
		self.question("set history size 1")
		self.question("set print demangle " + demangling)
		self.question("set confirm off")
		self.question("set verbose off")
		self.question("set language " + self.language)
		self.question("set width 0")

		# `free' may be relocated later - save its original address
		reply = self.question("output /x (void *)free")
		if reply.find("No symbol") >= 0:
			self.have_free = None
		else:
			self.have_free = int(reply, 0)

		self.__entry_point = None
		self.__entry_breakpoint = None



	def __del__(self):
		try:
			self.cleanup()
			self.__write("quit")
		except:
			pass

		del self.child


	# Helpers

	# Set language of debuggee.  Default is "c".
	def setLanguage(self, language):
		if language != "c" and language != "c++":
			raise UnsupportedLanguageError(language)
		else:
			self.language = language
			
	# Call the debugger.  To be overloaded in subclasses.
	def call(self):
		self.child = self.open_child(self.command(self.debuggee()))

	# Open a process.  To be overloaded in subclasses.
	def open_child(self, cmd):
		if self.logging:
			print ">> " + cmd
			sys.stdout.flush()
		return popen2.Popen3(cmd)

	# Return the name of the debuggee.
	def debuggee(self):
		return self.__debuggee

	# Return the name of the GDB command.
	def command(self, debuggee):
		return "gdb -nw -q " + debuggee + " 2>&1"

	# Set the `run' default argument
	def invoke(self, invocation):
		self.__invocation = invocation

	ENTRY_POINT_PATTERN = \
		re.compile(r"Entry\s+point:\s+(?P<entry_point>0x[0-9a-f]+)")

	# Return entry point
	def entry_point(self):
		if self.__entry_point is not None:
			return self.__entry_point
		
		target = self.question("info target")
		m = self.ENTRY_POINT_PATTERN.search(target)
		if m:
			self.__entry_point = m.group('entry_point')
		else:
			# Fallback: use `main' address
			self.__entry_point = self.question("output /x &main")

		return self.__entry_point
		

	# Start the debuggee using INVOCATION.  Use this method instead of
	# gdb.question("run"), as it allows arbitrary invocations.
	def run(self, invocation = None, timeout = None):
		# Hack: The overloaded `run' method in `StateGDB' is never
		# invoked, so we use this workaround.
		try:
			self.before_run()
		except:
			pass

		self.cleanup()

		if self.fetch_debuggee_pid:
			if self.__entry_breakpoint is not None:
				self.delete([self.__entry_breakpoint])

			entry_point = self.entry_point()
			self.__entry_breakpoint = self.break_at("*" + entry_point)
			self.commands(self.__entry_breakpoint,
						  [ "silent",
							"info program",
							"echo " + self.issued_pid_magic + "\\n",
							"cont" ])

			# For some reason, `enable delete' won't work :-(
			self.question("enable once " + `self.__entry_breakpoint`)

		if invocation is None:
			invocation = self.__invocation
		else:
			self.__invocation = invocation

		# INVOCATION can be None if we want to run without arguments
		if invocation is None or invocation == self.debuggee():
			return self.run_direct("", timeout)
		elif self.is_simple_invocation(invocation):
			args = invocation[invocation.index(" ") + 1:]
			return self.run_direct(args, timeout)
		else:
			return self.run_indirect(invocation, timeout)

	# Resume execution until program ends
	def resume(self, timeout = None):
		self.question("disable")
		return self.cont(timeout)

	def cont(self, timeout = None):
		return self.question("cont", timeout)

	NO_FINISH_PATTERN = \
		re.compile(r".* not meaningful in the outermost frame\.\n")

	# Finish current function (including the outermost frame)
	def finish(self, timeout = None):
		reply = self.question("finish", timeout)
		if self.NO_FINISH_PATTERN.match(reply):
			# GDB doesn't want us to finish `main', so here we go...
			return self.cont(timeout)

		return reply

	# Return initial messages
	def initial_messages(self):
		return self.__initial_messages

	# Kill the debugger process
	def kill_self(self, sig = signal.SIGTERM):
		self.kill(self.child.pid, sig)

	# Kill the debuggee and all its descendants
	def kill_debuggee(self, sig = signal.SIGTERM):
		if self.debuggee_pid is not None:
			self.kill(self.debuggee_pid, sig)

	# Kill the process PID
	def kill(self, pid, sig = signal.SIGTERM):
		print "Killing", pid
		try:
			os.kill(pid, sig)
		except OSError:
			pass                        # No such process

	# Load a new debuggee called NAME
	def load_debuggee(self, name):
		self.question("file " + name)

		# For some reason, `xilozafi' wants this.
		self.question("exec-file " + name)

		# Hack: After reloading, btmatchers intern variable $calls is undefined
		self.question("set var $calls = 0")

		# Hack: The overloaded `load_debuggee' method in `StateGDB' is
		# never invoked, so we use this workaround.
		try:
			self.after_load_debuggee()
		except:
			pass

	# Restore original
	def restore_original(self):
		if self.original_program is not None:
			self.question("shell mv -f " + sh_quote(self.original_program) +
						  " " + sh_quote(self.debuggee()))
			self.load_debuggee(self.debuggee())
			self.original_program = None

	# End of session
	def cleanup(self):
		self.restore_original()
		self.question("kill", self.cleanup_timeout)
		self.proxy_child  = None
		self.debuggee_pid = None
		self.question("shell rm -f " + sh_quote(self.debuggee_output_file()),
					  self.cleanup_timeout)
		self.disabled_functions = {}

	# Replace quoted parts of invocation
	def _stringless_invocation(self, invocation):
		SQ_STRING_PATTERN = re.compile("(\\\\')|'[^']*'")
		DQ_STRING_PATTERN = re.compile('(\\\\")|"([^"]|\\\\")*"')
		result = SQ_STRING_PATTERN.sub("'X'",invocation)
		result = DQ_STRING_PATTERN.sub('"X"',result)
		return result
			
	def is_simple_invocation(self, invocation):
		invocation = self._stringless_invocation(invocation)
		return ((invocation.startswith(self.debuggee() + " ") or
				 invocation.startswith("./" + self.debuggee() + " ")) and
				";" not in invocation and
				"|" not in invocation and
				"&" not in invocation)


	# Convert a list NUMS of integers to a space-separated string
	def numlist(self, nums):
		list = ""
		for num in nums:
			if list != "":
				list = list + " "
			list = list + `num`
		return list


	# Low-level interface

	# Write CMD to GDB
	def __write(self, cmd):
		if self.logging:
			print "-> " + cmd
			sys.stdout.flush()
		self.child.tochild.write(cmd + "\n")
		self.child.tochild.flush()

	# Read single line
	def __readline(self):
		line = self.child.fromchild.readline()
		return line

	PID_PATTERN = re.compile(".*(pid |child process |lwp )" +
							 "(?P<pid>[0-9][0-9]*)", re.IGNORECASE)

	# Read reply until prompt appears
	def __read_until_prompt(self):
		self.__reply_so_far = ""
		wait_for_issued_pid_magic = 0

		while not self.__reply_so_far.endswith(self.prompt):
			line = self.__readline()
			if self.logging:
				print "<- " + line,
				sys.stdout.flush()

			if line == '':
				raise EOFError

			self.__reply_so_far += line

			if self.fetch_debuggee_pid and self.debuggee_pid is None:
				# We still need the PID of the debuggee.
				m = self.PID_PATTERN.match(line)
				if m:
					self.debuggee_pid = int(m.group('pid'))
					wait_for_issued_pid_magic = 1

			if (wait_for_issued_pid_magic and
				self.__reply_so_far.endswith(self.issued_pid_magic + "\n")):
				# Ignore the preceding PID output
				self.__reply_so_far = ""
				wait_for_issued_pid_magic = 0


		# Cut off prompt and final newline
		self.__reply_so_far = self.__reply_so_far[:-len(self.prompt)]
		return self.__reply_so_far

	# Return the output read so far (for interrupts)
	def reply_so_far(self):
		return self.__reply_so_far


	# Mid-level interface

	# Send CMDLIST to GDB; return GDB's reply.
	# If TIMEOUT is set, raise a TimeOutError after TIMEOUT seconds.
	def question(self, cmdlist, timeout = None):
		#print cmdlist
		if not isinstance(cmdlist, type([])):
			cmdlist = [cmdlist]

		whole_reply = None
		for cmd in cmdlist:
			self.__write(cmd)            
			a = AlarmHandler.AlarmHandler(timeout)
			try:
				reply = self.__read_until_prompt()
			except AlarmHandler.TimeOutError:
				if whole_reply:
					self.__reply_so_far = whole_reply + self.__reply_so_far
				raise TimeOutError(timeout)
			del a

			if reply[:len(cmd)] == cmd:
				# Weed out echo
				reply = reply[len(cmd):]

			if not whole_reply:
				whole_reply = reply
			else:
				whole_reply += "\n" + reply
			
		#print whole_reply
		return whole_reply

	# Interrupt
	def interrupt(self, siglist = None):
		if self.logging:
			print "=> Interrupt"
			sys.stdout.flush()

		if siglist is None:
			siglist = [ signal.SIGHUP, signal.SIGKILL ]

		reply = ""
		a = None

		for sig in siglist:
			reply += self.reply_so_far()

			a = AlarmHandler.AlarmHandler(self.signal_timeout)
			try:
				self.kill_debuggee(sig)
				reply += self.__read_until_prompt()
				del a
				break
			except AlarmHandler.TimeOutError:
				del a
				continue
			except IOError:
				break
			except EOFError:
				break

		return reply


	FILE_PATTERN = re.compile(r"File\s+(?P<filename>.*):")
	FUNCTION_PATTERN = re.compile(r".*\s+(?P<name>[^ ]+)[(].*[)];")
	CDIR_PATTERN = re.compile(r"(.|\n)*Compilation directory is (?P<cdir>.*)")

	# High-level interface

	# Return list of debuggee symbols
	def all_symbols(self):
		break_cmd = "break "
		symbols = string.split(self.question("complete " + break_cmd), "\n")
		for i in range(0, len(symbols)):
			symbols[i] = symbols[i][len(break_cmd):]
		return symbols

	# Return list of (FILE, FUNCTION).  Caching.
	def _all_functions(self):
		if self.all_functions_cache is not None:
			return self.all_functions_cache
		
		current_file = None

		functions = []
		for line in self.question("info functions").split('\n'):
			m = self.FILE_PATTERN.match(line)
			if m is not None:
				current_file = m.group('filename')
			m = self.FUNCTION_PATTERN.match(line)
			if m is not None:
				functions.append((current_file, m.group('name')))

		self.all_functions_cache = functions
		return functions

	# Return list of source files.  Caching.
	def all_sources(self):
		if self.all_sources_cache is not None:
			return self.all_sources_cache

		sources = []
		for word in self.question("info sources").split(","):
			word = word.split()[-1]
			sources.append(word)

		self.all_sources_cache = sources
		return sources

	# Return list of debuggee functions.
	def all_functions(self):
		names = []
		for (file, function) in self._all_functions():
			name = file + ':' + function
			names.append(name)
		return names

	# Return list of debuggee functions with debugging information.
	def all_functions_with_debug_info(self):
		if self.all_functions_with_debug_info_cache is not None:
			return self.all_functions_with_debug_info_cache
		
		names = []
		for (file, function) in self._all_functions():
			name = file + ':' + function

			info_line = self.question("info line " + name)
			if info_line.startswith("Line "):
				names.append(name)

		self.all_functions_with_debug_info_cache = names
		return names


	# Break at LOCATION (a function, a line number, or a (FILE, LINE) pair);
	# return breakpoint number
	def break_at(self, location = None):
		hit = None
		file = None
		line = None
		function = None
		address = None

		if isinstance(location, type("")):
			if location.startswith('*'):
				address = location[1:]
			else:
				function = location
		elif isinstance(location, type(0)):
			line = location
		elif isinstance(location, type(())):
			(file, line) = location

		elif isinstance(location, type({})):
			for key in location.keys():
				if key == 'file':
					file = location[key]
				elif key == 'address':
					address = location[key]
				elif key == 'line':
					line = location[key]
				elif key == 'function':
					function = location[key]
				elif key == 'hit':
					hit = location[key]
				elif key == 'linehit':
					# not needed here, but this key is needed
					# in DDCIgor.py to insert this value into
					# table location
					pass
				else:
					assert 0

		arg = ""

		#Ordered: more specific location-descriptions are preferred
		if address:
			arg = '*' + address
		elif file and line:
			arg = file + ":" + `line`
		elif line:
			arg = `line`
		elif function:
			# A function name may be something like `foo.cc:operator='.
			# Be sure to quote the function name.
			file_prefix = None
			colon_index = function.find(':')
			if (colon_index >= 0 and
				colon_index + 1 < len(function) and
				function[colon_index + 1] != ':'):
				file_prefix = function[:colon_index]
				function = function[colon_index + 1:]

			arg = "'" + function + "'"
			if file_prefix is not None:
				arg = file_prefix + ":" + arg
	

		reply = self.question("break " + arg, self.set_break_timeout)

		# REPLY is something like `Breakpoint NR at ADDRESS'
		bp_index = reply.find("Breakpoint ")
		if bp_index < 0:
			raise NoSymbolsError, reply

		info = reply[bp_index:]
		bp_nr = string.atoi((string.split(string.replace(info,","," ")))[1])

		if hit:
			self.question("ignore " + `bp_nr` + " " + `hit - 1`,self.set_break_timeout)

		return bp_nr

	# Define sequence of commands for given breakpoint
	def commands(self, breakpoint, cmds):
		cmd = "commands " + `breakpoint` + "\n"
		for c in cmds:
			cmd = cmd + c + "\n"
		cmd = cmd + "end"
		self.question(cmd)

	# Return compilation directory of LOCATION
	def cdir(self, location = None):
		if location is not None:
			self.question("list " + location)
		reply = self.question("info source")
		m = self.CDIR_PATTERN.match(reply)
		if m is None:
			return None
		return m.group('cdir')

	# Enable the given breakpoints
	def enable(self, breakpoints):
		if len(breakpoints) > 0:
			self.question("enable " + self.numlist(breakpoints))

	# Disable the given breakpoints
	def disable(self, breakpoints):
		if len(breakpoints) > 0:
			self.question("disable " + self.numlist(breakpoints))

	# Enable all the breakpoints
	def enableAll(self):
		return self.question("enable")

	# Disable all the breakpoints
	def disableAll(self):
		self.question("disable")

	# Delete the given breakpoints
	def delete(self, breakpoints):
		if len(breakpoints) > 0:
			self.question("delete " + self.numlist(breakpoints))

	# Fetch byte at NAME
	def peek(self, name):
		return int(self.question("output /x *((char *)" +  name + ")"), 0)

	# Store byte VALUE at NAME
	def poke(self, name, value):
		self.question("set variable *((char *)" + name + ") = " + hex(value))

	# Make function NAME a no-op.
	def disable_function(self, name):
		# We disable a function by writing a `ret' opcode at its address.
		# This is much preferable than setting a breakpoint with commands,
		# because GDB tends to relocate breakpoints.
		if self.disabled_functions.has_key(name):
			return                      # Already disabled

		RET_OPCODE = 0xc3               # On i386
		old_opcode = self.peek(name)
		self.poke(name, RET_OPCODE)
		self.disabled_functions[name] = old_opcode

	# Restore function NAME
	def enable_function(self, name):
		if not self.disabled_functions.has_key(name):
			return                      # Not disabled
		
		old_opcode = disabled_functions[name]
		self.poke(name, old_opcode)
		del disabled_functions[name]

	# Disable `free' if it is dynamically loaded
	def disable_dynamic_free(self):
		if self.have_free is None:
			return

		# In Linux, all dynamic symbols are located in segment 0x40...
		definition = self.question("output free")
		if definition.find("0x4") >= 0:
			self.disable_function(hex(self.have_free))

	# Specials for starting programs

	def debuggee_original_file(self):
		return self.debuggee() + ".OrIg"

	def debuggee_output_file(self):
		return self.debuggee() + ".OuT"

	def debuggee_output(self, timeout = None):
		# If the program is still running, kill it
		self.question("kill")
		
		# Wait for the queue to terminate
		if self.proxy_child is not None:
			a = AlarmHandler.AlarmHandler(timeout)
			try:
				self.proxy_child.wait()
			except AlarmHandler.TimeOutError:
				pass

			# Close queue
			self.proxy_child = None

		return self.question("shell cat " +
							 sh_quote(self.debuggee_output_file()))

	# Start program from the debugger.
	def run_direct(self, args, timeout):
		if self._stringless_invocation(args).find(">") < 0:
			args += " > " + self.debuggee_output_file() + " 2>&1"
		return self.question("run " + args, timeout)

	# Start program indirectly, using an invocation command.
	def run_indirect(self, invocation, timeout):
		self.original_program = self.debuggee_original_file()
		self.output_file = self.debuggee_output_file()

		# Here's how this works.  We replace the original program by a
		# proxy script.  This proxy script forwards all its input to a
		# named pipe.  This pipe is read by the debuggee within GDB.
		# The debuggee output is sent to another named pipe, which is
		# then read by the proxy script and forwarded to its output.

		# FIXME: Make the script exit with the same return tcas as the
		# original debuggee.

		# FIXME: calling this script with embedded quotes does not work,
		# eg. "replace '*' '%@&a' < file" leads to a finalized call at &

		proxy_script = \
"""
#!/bin/sh

in_pipe=/tmp/gdb_in$$
out_pipe=/tmp/gdb_out$$
err_pipe=/tmp/gdb_err$$

mkfifo $in_pipe $out_pipe $err_pipe
echo "PiPeS" $in_pipe $out_pipe $err_pipe >&31
echo "ArGs" "$@" >&31

cat < $out_pipe     &
cat < $err_pipe >&2 &
cat > $in_pipe      &
wait

rm -f $in_pipe $out_pipe $err_pipe
"""

		self.question("shell mv -f " + sh_quote(self.debuggee()) + " " +
					  sh_quote(self.original_program))

		for line in proxy_script.splitlines():
			if line:
				self.question("shell echo " + sh_quote(line) +
							  " >> " + sh_quote(self.debuggee()))

		self.question("shell chmod 770 " + sh_quote(self.debuggee()))
		self.question("shell touch -r " + sh_quote(self.original_program) +
					  " " + sh_quote(self.debuggee()))

		invocation_cmd = ("(" + invocation + ") 30<&0 31>&1 32>&2" +
						  " > " + self.output_file + " 2>&1")

		self.proxy_child = self.open_child(invocation_cmd)

		a = AlarmHandler.AlarmHandler(self.invocation_timeout)
		try:
			pipes = self.proxy_child.fromchild.readline().split()
		except AlarmHandler.TimeOutError:
			pipes = []

		if len(pipes) == 0 or pipes[0] != "PiPeS":
			output = self.debuggee_output(self.invocation_timeout)
			self.cleanup()
			raise NotInvokedError, output

		in_pipe = pipes[1]
		out_pipe = pipes[2]
		err_pipe = pipes[3]

		try:
			args = self.proxy_child.fromchild.readline().split()
		except AlarmHandler.TimeOutError:
			args = []

		if len(args) == 0 or args[0] != "ArGs":
			output = self.debuggee_output(self.invocation_timeout)
			self.cleanup()
			raise NotInvokedError, output

		del a

		args = string.join(args[1:], " ")

		self.load_debuggee(self.original_program)
		run_cmd = ("run " + args + " < " + in_pipe + " > " + out_pipe + 
				   " 2> " + err_pipe)
		return self.question(run_cmd, timeout)


	# Interactive mode. Useful for debugging.
	def interactive(self):
		import readline
		import rlcompleter

		readline.parse_and_bind("tab: complete")

		def nop():
			pass

		self.completions = []
		def completer(text, state):
			buf = readline.get_line_buffer()
			if state == 0:
				cmd = "complete " + buf
				completions = self.question(cmd)
				self.completions = string.split(completions, "\n")

			if state < len(self.completions) - 1:
				completion = self.completions[state][readline.get_begidx():]
				return completion
			return None

		readline.set_completer(completer)
		
		saved_logging = self.logging
		self.logging = 0
		resume = "#"
		if self.verbose:
			print "Entering interactive mode.  Enter",
			print `resume` + " to resume."
		sys.stdout.flush()
		while 1:
			try:
				cmd = raw_input("(gdb) ")
			except EOFError:
				cmd = resume
			except IOError:
				break
			except KeyboardInterrupt:
				continue

			if cmd == resume:
				break
			function = self.interactive_functions.get(cmd, nop)
			if function != nop:
				function()
				continue

			try:
				sys.stdout.write(self.question(cmd))
			except EOFError:
				break
			except IOError:
				break
			except KeyboardInterrupt:
				sys.stdout.write(self.interrupt([signal.SIGINT]))
		
		self.logging = saved_logging

	def set_interactive_functions(self, interactive_functions):
		self.interactive_functions = interactive_functions


if __name__ == '__main__':

	if len(sys.argv) == 1:
		gdb = GDB()
		gdb.interactive()
	else:
		GDB.logging = 1
		
		gdb = GDB(sys.argv[1])
		# print "All functions:", gdb.all_functions()
		# print "All debugging functions:", gdb.all_functions_with_debug_info()
		print gdb.initial_messages()

		gdb.logging = 1

		if len(sys.argv) >= 3:
			gdb.run(sys.argv[2], 10)
			output = `gdb.debuggee_output(2)`

			print "Output:", output

		del gdb
