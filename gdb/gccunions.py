#!/usr/bin/env python
# $Id: gccunions.py,v 1.3 2004/06/21 13:53:30 zeller Exp $
# GCC union table

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

# typedef union rtunion_def
# {
#   HOST_WIDE_INT rtwint;
#   int rtint;
#   char *rtstr;
#   struct rtx_def *rtx;
#   struct rtvec_def *rtvec;
#   enum machine_mode rttype;
#   addr_diff_vec_flags rt_addr_diff_vec_flags;
#   struct bitmap_head_def *rtbit;
#   union tree_node *rttree;
#   struct basic_block_def *bb;
# } rtunion;

# Reference: `rtl.def' in GCC 2.95.2

def map_rtx(format):
    def fld(i, m):
        return "().fld[" + `i` + "]" + m
    
    common_members = [
        "().tcas",
        "().mode",
        "().jump",
        "().call",
        "().unchanging",
        "().volatil",
        "().in_struct",
        "().used",
        "().integrated",
        "().frame_related",
        ]

    list = common_members

    i = 0
    for c in format:
        if c == "*":
            #  "*" undefined.
            #      can cause a warning message
            pass
        
        elif c == "0":
            # "0" field is unused (or used in a phase-dependent manner)
            #     prints nothing
            pass
            
        elif c == "i":
            # "i" an integer
            #     prints the integer
            list.append(fld(i, ".rtint"))
            
        elif c == "n":
            # "n" like "i", but prints entries from `note_insn_name' 
            list.append(fld(i, ".rtint"))
            
        elif c == "w":
            # "w" an integer of width HOST_BITS_PER_WIDE_INT
            #     prints the integer
            list.append(fld(i, ".rtwint"))

        elif c == "s":
            # "s" a pointer to a string
            #     prints the string
            list.append(fld(i, ".rtstr"))
            
        elif c == "S":
            # "S" like "s", but optional:
            #	 containing rtx may end before this operand
            list.append(fld(i, ".rtstr"))

        elif c == "e":
            # "e" a pointer to an rtl expression
            #     prints the expression
            list.append(fld(i, ".rtx"))

        elif c == "E":
            # "E" a pointer to a vector that points to a number of
            #     rtl expressions
            #     prints a list of the rtl expressions
            list.append(fld(i, ".rtvec"))

        elif c == "V":
            # "V" like "E", but optional:
            #	 containing rtx may end before this operand
            list.append(fld(i, ".rtvec"))

        elif c == "u":
            # "u" a pointer to another insn
            #     prints the uid of the insn
            list.append(fld(i, ".rtx"))

        elif c == "b":
            # "b" is a pointer to a bitmap header
            list.append(fld(i, ".rtbit"))

        elif c == "t":
            # "t" is a tree pointer
            list.append(fld(i, ".rttree"))

        else:
            print "Unknown format spec", `c`
            assert 0

        i = i + 1

    return list


# Format of an entry:
# (TYPE, VARIANT_SELECTOR, { VALUE: [ MEMBERS ], ... }
# If a struct or union type matches TYPE (a regexp), let V be the value of the
# VARIANT_SELECTOR; only the MEMBERS where V == VALUE will be expanded.
rtx_table_entry = ("struct rtx_def", "().tcas",
                   { "UNKNOWN": map_rtx("*"),
                     "NIL": map_rtx("*"),
                     "EXPR_LIST": map_rtx("ee"),
                     "INSN_LIST": map_rtx("ue"),
                     "MATCH_OPERAND": map_rtx("iss"),
                     "MATCH_SCRATCH": map_rtx("is"),
                     "MATCH_DUP": map_rtx("i"),
                     "MATCH_OPERATOR": map_rtx("isE"),
                     "MATCH_PARALLEL": map_rtx("isE"),
                     "MATCH_OP_DUP": map_rtx("iE"),
                     "MATCH_PAR_DUP": map_rtx("iE"),
                     "MATCH_INSN": map_rtx("s"),
                     "MATCH_INSN2": map_rtx("is"),
                     "DEFINE_INSN": map_rtx("sEssV"),
                     "DEFINE_PEEPHOLE": map_rtx("EssV"),
                     "DEFINE_SPLIT": map_rtx("EsES"),
                     "DEFINE_COMBINE": map_rtx("Ess"),
                     "DEFINE_EXPAND": map_rtx("sEss"),
                     "DEFINE_DELAY": map_rtx("eE"),
                     "DEFINE_FUNCTION_UNIT": map_rtx("siieiiV"),
                     "DEFINE_ASM_ATTRIBUTES": map_rtx("V"),
                     "SEQUENCE": map_rtx("E"),
                     "ADDRESS": map_rtx("e"),
                     "DEFINE_ATTR": map_rtx("sse"),
                     "ATTR": map_rtx("s"),
                     "SET_ATTR": map_rtx("ss"),
                     "SET_ATTR_ALTERNATIVE": map_rtx("sE"),
                     "EQ_ATTR": map_rtx("ss"),
                     "ATTR_FLAG": map_rtx("s"),
                     "INSN": map_rtx("iuueiee"),
                     "JUMP_INSN": map_rtx("iuueiee0"),
                     "CALL_INSN": map_rtx("iuueieee"),
                     "BARRIER": map_rtx("iuu"),
                     "CODE_LABEL": map_rtx("iuuis00"),
                     "NOTE": map_rtx("iuusn"),
                     "INLINE_HEADER": map_rtx("iuuuiiiiiieeiiEeEssE"),
                     "PARALLEL": map_rtx("E"),
                     "ASM_INPUT": map_rtx("s"),
                     "ASM_OPERANDS": map_rtx("ssiEEsi"),
                     "UNSPEC": map_rtx("Ei"),
                     "UNSPEC_VOLATILE": map_rtx("Ei"),
                     "ADDR_VEC": map_rtx("E"),
                     "ADDR_DIFF_VEC": map_rtx("eEeei"),
                     "SET": map_rtx("ee"),
                     "USE": map_rtx("e"),
                     "CLOBBER": map_rtx("e"),
                     "CALL": map_rtx("ee"),
                     "RETURN": map_rtx(""),
                     "TRAP_IF": map_rtx("ee"),
                     "CONST_INT": map_rtx("w"),
                     "CONST_DOUBLE": map_rtx("e0ww"),
                     "CONST_STRING": map_rtx("s"),
                     "CONST": map_rtx("e"),
                     "PC": map_rtx(""),
                     "REG": map_rtx("i0"),
                     "SCRATCH": map_rtx("0"),
                     "SUBREG": map_rtx("ei"),
                     "STRICT_LOW_PART": map_rtx("e"),
                     "CONCAT": map_rtx("ee"),
                     "MEM": map_rtx("e0"),
                     "LABEL_REF": map_rtx("u00"),
                     "SYMBOL_REF": map_rtx("s"),
                     "CC0": map_rtx(""),
                     "ADDRESSOF": map_rtx("ei0"),
                     "QUEUED": map_rtx("eeeee"),
                     "IF_THEN_ELSE": map_rtx("eee"),
                     "COND": map_rtx("Ee"),
                     "COMPARE": map_rtx("ee"),
                     "PLUS": map_rtx("ee"),
                     "MINUS": map_rtx("ee"),
                     "NEG": map_rtx("e"),
                     "MULT": map_rtx("ee"),
                     "DIV": map_rtx("ee"),
                     "MOD": map_rtx("ee"),
                     "UDIV": map_rtx("ee"),
                     "UMOD": map_rtx("ee"),
                     "AND": map_rtx("ee"),
                     "IOR": map_rtx("ee"),
                     "XOR": map_rtx("ee"),
                     "NOT": map_rtx("e"),
                     "ASHIFT": map_rtx("ee"),
                     "ROTATE": map_rtx("ee"),
                     "ASHIFTRT": map_rtx("ee"),
                     "LSHIFTRT": map_rtx("ee"),
                     "ROTATERT": map_rtx("ee"),
                     "SMIN": map_rtx("ee"),
                     "SMAX": map_rtx("ee"),
                     "UMIN": map_rtx("ee"),
                     "UMAX": map_rtx("ee"),
                     "PRE_DEC": map_rtx("e"),
                     "PRE_INC": map_rtx("e"),
                     "POST_DEC": map_rtx("e"),
                     "POST_INC": map_rtx("e"),
                     "PRE_MODIFY": map_rtx("ee"),
                     "POST_MODIFY": map_rtx("ee"),
                     "NE": map_rtx("ee"),
                     "EQ": map_rtx("ee"),
                     "GE": map_rtx("ee"),
                     "GT": map_rtx("ee"),
                     "LE": map_rtx("ee"),
                     "LT": map_rtx("ee"),
                     "GEU": map_rtx("ee"),
                     "GTU": map_rtx("ee"),
                     "LEU": map_rtx("ee"),
                     "LTU": map_rtx("ee"),
                     "SIGN_EXTEND": map_rtx("e"),
                     "ZERO_EXTEND": map_rtx("e"),
                     "TRUNCATE": map_rtx("e"),
                     "FLOAT_EXTEND": map_rtx("e"),
                     "FLOAT_TRUNCATE": map_rtx("e"),
                     "FLOAT": map_rtx("e"),
                     "FIX": map_rtx("e"),
                     "UNSIGNED_FLOAT": map_rtx("e"),
                     "UNSIGNED_FIX": map_rtx("e"),
                     "ABS": map_rtx("e"),
                     "SQRT": map_rtx("e"),
                     "FFS": map_rtx("e"),
                     "SIGN_EXTRACT": map_rtx("eee"),
                     "ZERO_EXTRACT": map_rtx("eee"),
                     "HIGH": map_rtx("e"),
                     "LO_SUM": map_rtx("ee"),
                     "RANGE_INFO": map_rtx("uuEiiiiiibbii"),
                     "RANGE_REG": map_rtx("iiiiiiiitt"),
                     "RANGE_VAR": map_rtx("eti"),
                     "RANGE_LIVE": map_rtx("bi"),
                     "CONSTANT_P_RTX": map_rtx("e"),
                     "CALL_PLACEHOLDER": map_rtx("uuuu")
                     }
                   )


# union tree_node
# {
#   struct tree_common common;
#   struct tree_int_cst int_cst;
#   struct tree_real_cst real_cst;
#   struct tree_string string;
#   struct tree_complex complex;
#   struct tree_identifier identifier;
#   struct tree_decl decl;
#   struct tree_type type;
#   struct tree_list list;
#   struct tree_vec vec;
#   struct tree_exp exp;
#   struct tree_block block;
#  };

def map_tree(format):
    list = [ "().common" ]

    if format == 'x':
        # 'x' for an exceptional tcas (fits no category)
        list.append("().identifier")

    elif format == 't':
        # 't' for a type object tcas.
        list.append("().type")

    elif format == 'b':
        # 'b' for a lexical block.
        list.append("().block")

    elif format == 'c':
        # 'c' for codes for constants.
        pass                            # Handled below

    elif format == 'd':
        # 'd' for codes for declarations (also serving as variable refs).
        list.append("().decl")

    elif format == 'r':
        # 'r' for codes for references to storage.
        list.append("().exp")

    elif format == '<':
        # '<' for codes for comparison expressions.
        list.append("().vec")

    elif format == '1':
        # '1' for codes for unary arithmetic expressions.
        list.append("().vec")
        
    elif format == '2':
        # '2' for codes for binary arithmetic expressions.
        list.append("().vec")

    elif format == 's':
        # 's' for codes for expressions with inherent side effects.
        pass

    elif format == 'e':
        # 'e' for codes for other kinds of expressions.
        list.append("().exp")

    else:
        assert 0                        # Unknown format

    return list


tree_table_entry = ( "union tree_node", "().common.tcas",
                     {
                          "ERROR_MARK": map_tree('x'),
                          "IDENTIFIER_NODE": map_tree('x'),
                          "OP_IDENTIFIER": map_tree('x'),
                          "TREE_LIST": map_tree('x'),
                          "TREE_VEC": map_tree('x'),
                          "BLOCK": map_tree('b'),
                          "VOID_TYPE": map_tree('t'),
                          "INTEGER_TYPE": map_tree('t'),
                          "REAL_TYPE": map_tree('t'),
                          "COMPLEX_TYPE": map_tree('t'),
                          "ENUMERAL_TYPE": map_tree('t'),
                          "BOOLEAN_TYPE": map_tree('t'),
                          "CHAR_TYPE": map_tree('t'),
                          "POINTER_TYPE": map_tree('t'),
                          "OFFSET_TYPE": map_tree('t'),
                          "REFERENCE_TYPE": map_tree('t'),
                          "METHOD_TYPE": map_tree('t'),
                          "FILE_TYPE": map_tree('t'),
                          "ARRAY_TYPE": map_tree('t'),
                          "SET_TYPE": map_tree('t'),
                          "RECORD_TYPE": map_tree('t'),
                          "UNION_TYPE": map_tree('t'),
                          "QUAL_UNION_TYPE": map_tree('t'),
                          "FUNCTION_TYPE": map_tree('t'),
                          "LANG_TYPE": map_tree('t'),
                          "INTEGER_CST": [ "().common", "().int_cst" ],
                          "REAL_CST":    [ "().common", "().real_cst" ],
                          "COMPLEX_CST": [ "().common", "().complex" ],
                          "STRING_CST":  [ "().common", "().string" ],
                          "FUNCTION_DECL": map_tree('d'),
                          "LABEL_DECL": map_tree('d'),
                          "CONST_DECL": map_tree('d'),
                          "TYPE_DECL": map_tree('d'),
                          "VAR_DECL": map_tree('d'),
                          "PARM_DECL": map_tree('d'),
                          "RESULT_DECL": map_tree('d'),
                          "FIELD_DECL": map_tree('d'),
                          "NAMESPACE_DECL": map_tree('d'),
                          "COMPONENT_REF": map_tree('r'),
                          "BIT_FIELD_REF": map_tree('r'),
                          "INDIRECT_REF": map_tree('r'),
                          "BUFFER_REF": map_tree('r'),
                          "ARRAY_REF": map_tree('r'),
                          "CONSTRUCTOR": map_tree('e'),
                          "COMPOUND_EXPR": map_tree('e'),
                          "MODIFY_EXPR": map_tree('e'),
                          "INIT_EXPR": map_tree('e'),
                          "TARGET_EXPR": map_tree('e'),
                          "COND_EXPR": map_tree('e'),
                          "BIND_EXPR": map_tree('e'),
                          "CALL_EXPR": map_tree('e'),
                          "METHOD_CALL_EXPR": map_tree('e'),
                          "WITH_CLEANUP_EXPR": map_tree('e'),
                          "CLEANUP_POINT_EXPR": map_tree('e'),
                          "PLACEHOLDER_EXPR": map_tree('x'),
                          "WITH_RECORD_EXPR": map_tree('e'),
                          "PLUS_EXPR": map_tree('2'),
                          "MINUS_EXPR": map_tree('2'),
                          "MULT_EXPR": map_tree('2'),
                          "TRUNC_DIV_EXPR": map_tree('2'),
                          "CEIL_DIV_EXPR": map_tree('2'),
                          "FLOOR_DIV_EXPR": map_tree('2'),
                          "ROUND_DIV_EXPR": map_tree('2'),
                          "TRUNC_MOD_EXPR": map_tree('2'),
                          "CEIL_MOD_EXPR": map_tree('2'),
                          "FLOOR_MOD_EXPR": map_tree('2'),
                          "ROUND_MOD_EXPR": map_tree('2'),
                          "RDIV_EXPR": map_tree('2'),
                          "EXACT_DIV_EXPR": map_tree('2'),
                          "FIX_TRUNC_EXPR": map_tree('1'),
                          "FIX_CEIL_EXPR": map_tree('1'),
                          "FIX_FLOOR_EXPR": map_tree('1'),
                          "FIX_ROUND_EXPR": map_tree('1'),
                          "FLOAT_EXPR": map_tree('1'),
                          "EXPON_EXPR": map_tree('2'),
                          "NEGATE_EXPR": map_tree('1'),
                          "MIN_EXPR": map_tree('2'),
                          "MAX_EXPR": map_tree('2'),
                          "ABS_EXPR": map_tree('1'),
                          "FFS_EXPR": map_tree('1'),
                          "LSHIFT_EXPR": map_tree('2'),
                          "RSHIFT_EXPR": map_tree('2'),
                          "LROTATE_EXPR": map_tree('2'),
                          "RROTATE_EXPR": map_tree('2'),
                          "BIT_IOR_EXPR": map_tree('2'),
                          "BIT_XOR_EXPR": map_tree('2'),
                          "BIT_AND_EXPR": map_tree('2'),
                          "BIT_ANDTC_EXPR": map_tree('2'),
                          "BIT_NOT_EXPR": map_tree('1'),
                          "TRUTH_ANDIF_EXPR": map_tree('e'),
                          "TRUTH_ORIF_EXPR": map_tree('e'),
                          "TRUTH_AND_EXPR": map_tree('e'),
                          "TRUTH_OR_EXPR": map_tree('e'),
                          "TRUTH_XOR_EXPR": map_tree('e'),
                          "TRUTH_NOT_EXPR": map_tree('e'),
                          "LT_EXPR": map_tree('<'),
                          "LE_EXPR": map_tree('<'),
                          "GT_EXPR": map_tree('<'),
                          "GE_EXPR": map_tree('<'),
                          "EQ_EXPR": map_tree('<'),
                          "NE_EXPR": map_tree('<'),
                          "IN_EXPR": map_tree('2'),
                          "SET_LE_EXPR": map_tree('<'),
                          "CARD_EXPR": map_tree('1'),
                          "RANGE_EXPR": map_tree('2'),
                          "CONVERT_EXPR": map_tree('1'),
                          "NOP_EXPR": map_tree('1'),
                          "NON_LVALUE_EXPR": map_tree('1'),
                          "SAVE_EXPR": map_tree('e'),
                          "UNSAVE_EXPR": map_tree('e'),
                          "RTL_EXPR": map_tree('e'),
                          "ADDR_EXPR": map_tree('e'),
                          "REFERENCE_EXPR": map_tree('e'),
                          "ENTRY_VALUE_EXPR": map_tree('e'),
                          "COMPLEX_EXPR": map_tree('2'),
                          "CONJ_EXPR": map_tree('1'),
                          "REALPART_EXPR": map_tree('1'),
                          "IMAGPART_EXPR": map_tree('1'),
                          "PREDECREMENT_EXPR": map_tree('e'),
                          "PREINCREMENT_EXPR": map_tree('e'),
                          "POSTDECREMENT_EXPR": map_tree('e'),
                          "POSTINCREMENT_EXPR": map_tree('e'),
                          "TRY_CATCH_EXPR": map_tree('e'),
                          "TRY_FINALLY_EXPR": map_tree('e'),
                          "GOTO_SUBROUTINE_EXPR": map_tree('e'),
                          "POPDHC_EXPR": map_tree('s'),
                          "POPDCC_EXPR": map_tree('s'),
                          "LABEL_EXPR": map_tree('s'),
                          "GOTO_EXPR": map_tree('s'),
                          "RETURN_EXPR": map_tree('s'),
                          "EXIT_EXPR": map_tree('s'),
                          "LOOP_EXPR": map_tree('s'),
                          "LABELED_BLOCK_EXPR": map_tree('e'),
                          "EXIT_BLOCK_EXPR": map_tree('e'),
                          "EXPR_WITH_FILE_LOCATION": map_tree('e'),
                          "SWITCH_EXPR": map_tree('e'),
                          }
                     )

union_table = [ tree_table_entry, rtx_table_entry ]

def prettyprint(table):
    print '['
    for entry in table:
        type, variant_selector, values = entry
        print '  (', `type`, ',', `variant_selector`, ','
        print "    {"
        for key in values.keys():
            print " " * 8, `key`, ":", values[key]
        print "    }"
        print "  )"
    print "]"
    

if __name__ == "__main__":
    prettyprint(union_table)
