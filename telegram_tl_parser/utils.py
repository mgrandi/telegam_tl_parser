import logging

import pyparsing

logger = logging.getLogger(__name__)
pplogger = logger.getChild("pyparsing")

def strip_margin(string:str, preserve_newlines:bool=False, strip_characters:str="|") -> str:
    ''' given a multi line string, for each line, remove the range from the beginning
    of the string to the margin character(s), and then return it, optionally separated by
    newlines or just spaces

    given the string:

    x = """
        |hey
        |there"""

    strip_margin(x) returns `hey there`
    strip_margin(x, True) returns

    `hey
    there`

    @param string - the string to strip the margins of
    @param preserve_newlines - if true, we combine the results with a `\n`, if
        false, we combine them with a space character instead
    @param strip_characters - the characters to use as a margin character
    @return a string with the margins stripped and optionally the newlines

    '''

    line_list = string.split("\n")

    result_list = []

    for iter_line in line_list:

        if not iter_line:
            continue

        elif strip_characters in iter_line:

            pos = iter_line.find(strip_characters)
            strip_chars_len = len(strip_characters)

            stripped = iter_line[pos + strip_chars_len:]
            result_list.append(stripped)

        else:

            result_list.append(iter_line)

    if preserve_newlines:
        return "\n".join(result_list)
    else:
        return " ".join(result_list)

def pyparsingLoggingStartDebugAction(instring, loc, expr):

    row = pyparsing.lineno(loc, instring)
    col = pyparsing.col(loc, instring)

    pplogger.debug("Match Start: expr: `%s` at loc `%s`, row: `%d`, col: `%d`",
        expr, loc, row, col)


def pyparsingLoggingSuccessDebugAction(instring, startloc, endloc, expr, toks):

    row_start = pyparsing.lineno(startloc, instring)
    col_start = pyparsing.col(startloc, instring)

    row_end = pyparsing.lineno(endloc, instring)
    col_end = pyparsing.col(endloc, instring)

    pplogger.debug(strip_margin('''Match Success: expr: `%s`, startLoc: `%s`,
        | startRow: `%s`, startCol: `%s`, endLoc: `%s`, endRow: `%s`, endCol:
        | `%s`, -> toks: `%s` tokens'''),
        expr,
        startloc,
        row_start,
        col_start,
        endloc,
        row_end,
        col_end,
        len(toks.asList()))


def pyparsingLoggingExceptionDebugAction(instring, loc, expr, exc):

    row = pyparsing.lineno(loc, instring)
    col = pyparsing.col(loc, instring)

    pplogger.error("Caught Exception: expr: `%s`, loc: `%s`,  row: `%d`, col: `%d`, exception: `%s`",
        expr, loc, row, col, exc)


def setLoggingDebugActionForParserElement(parser_element:pyparsing.ParserElement) -> None:
    '''
    helper function to set up the custom debug actions for a ParserElement with our
    own functions that use the logging framework rather than `print()`

    this also calls setDebug(True) for the parser element as well
    '''

    parser_element.setDebug(True)

    parser_element.setDebugActions(
        pyparsingLoggingStartDebugAction,
        pyparsingLoggingSuccessDebugAction,
        pyparsingLoggingExceptionDebugAction)