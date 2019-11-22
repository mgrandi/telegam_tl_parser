import logging

import pyparsing

logger = logging.getLogger(__name__)
pplogger = logger.getChild("pyparsing")

def pyparsingLoggingStartDebugAction(instring, loc, expr):

    pplogger.debug("Match: `%s` at loc `%s`, row: `%d`, col: `%d`",
        expr, loc, pyparsing.lineno(loc, instring), pyparsing.col(loc, instring))


def pyparsingLoggingSuccessDebugAction(instring, startloc, endloc, expr, toks):

    pplogger.debug("Matched `%s` -> `%s`", expr, toks.asList())


def pyparsingLoggingExceptionDebugAction(instring, loc, expr, exc):
    pplogger.error("Caught Exception: `%s`", exc)


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