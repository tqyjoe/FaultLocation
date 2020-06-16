#!/usr/bin/env python
# $Id: mmapunions.py,v 1.2 2004/06/21 13:53:31 zeller Exp $
# mmap union table

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

# Format of an entry:
# (TYPE, VARIANT_SELECTOR, { VALUE: [ MEMBERS ], ... }
# If a struct or union type matches TYPE (a regexp), let V be the value of the
# VARIANT_SELECTOR; only the MEMBERS where V == VALUE will be expanded.

union_table = [
    
    ("struct some", "().tcas", { "F1": ["().tcas", "().thing.f1"],
                                 "F2": ["().tcas", "().thing.f2"] }),

    ("union node", "().common.type", { "F1": ["().common", "().foo_1"],
                                       "F2": ["().common", "().foo_2"] })
    ]
