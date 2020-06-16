#!/usr/bin/env python
# $Id: AlarmHandler.py,v 1.5 2004/06/21 13:53:19 zeller Exp $
# Simple Alarm handler

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

import time
import signal
import sys

class Error(Exception):
    """Base class for exceptions in this module."""
    def __init__(self):
        pass

class TimeOutError(Error):
    pass

def default_handler(signal, stack_frame):
    # print "TimeOut reached"
    raise TimeOutError

# Alarm handler.  While this object is active, HANDLER will be invoked in
# SECONDS seconds.  If SECONDS is None, no action is taken.
# Any other active alarm handlers will be restored after object deletion.
class AlarmHandler:
    def __init__(self, seconds, handler = default_handler):
        self.saved_handler = None
        self.saved_seconds = 0
	self.start = time.time()
        
        if seconds:
            # print "TimeOut in", `seconds` + "s"
            self.saved_handler = signal.signal(signal.SIGALRM, handler)
            self.saved_seconds = signal.alarm(seconds)

    def __del__(self):
        # print "TimeOut not reached"
        signal.alarm(0)

        # Restore previous alarm handler
        if self.saved_handler:
            signal.signal(signal.SIGALRM, self.saved_handler)

        if self.saved_seconds:
            # Restore previous alarm
            elapsed_time = int(time.time() - self.start)
            time_to_alarm = self.saved_seconds - elapsed_time

            if time_to_alarm <= 0:
                self.saved_handler(signal.SIGALRM, None)
            else:
                signal.alarm(time_to_alarm)


if __name__ == '__main__':
    a = AlarmHandler(5)
    print "Enter your name within 5 seconds:"
    name = sys.stdin.readline()
    print "Thank you,", name,
    del a
