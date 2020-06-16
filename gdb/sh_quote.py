#!/usr/bin/env python
# $Id: sh_quote.py,v 1.2 2004/06/21 13:53:32 zeller Exp $

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

# Quote string such that it can be used as sh argument.
# sh_quote("a>b") = "'a>b'"
def sh_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"

