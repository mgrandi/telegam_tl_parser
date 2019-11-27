import pathlib
import typing
import logging

import attr
import pyparsing

import telegram_tl_parser.utils as utils
from telegram_tl_parser.model import TlParameter, TlTypeDefinition, TlFunctionDefinition, TlFileDefinition

logger = logging.getLogger(__name__)

RESULT_NAME_SOURCE_LINE = "source_line"
RESULT_NAME_PARAMS = "params"
RESULT_NAME_PARAM_NAME = "param_name"
RESULT_NAME_PARAM_TYPE = "param_type"
RESULT_NAME_CLASS_NAME = "class_name"
RESULT_NAME_EXTENDS_FROM_ABC = "extends_from_abc"
RESULT_NAME_RETURN_TYPE = "return_type"


class Parser:

    def __init__(self):

        pass




    def parse(self, tl_file_path:pathlib.Path,
        skip_n_lines:int,
        pyparsing_debug_logging_enabled:bool) -> typing.Sequence[TlFileDefinition]:
        '''

        @param tl_file_path the Path to the .tl file we are parsing
        '''

        logger.info("parsing file: `%s`", tl_file_path)
        logger.info("skipping `%s` lines from the start of the file", skip_n_lines)

        # See `notes.md` for notes on the structure of the file
        # and see `pyparsing_notes.md` for notes on pyparsing stuff
        skip_line = pyparsing.SkipTo(pyparsing.lineEnd, include=True)

        comment = pyparsing.Literal('//') - pyparsing.restOfLine

        class_name = pyparsing.Word(pyparsing.alphanums)
        equal_sign_literal = pyparsing.Literal("=")

        param_name = pyparsing.Word(pyparsing.alphanums + "_")
        colon_literal_suppressed = pyparsing.Literal(":").suppress()
        # need the angle brackets for stuff like `vector<String>`
        param_type =  pyparsing.Word(pyparsing.alphanums + "<>")

        param_listing = pyparsing.Group(
            param_name(RESULT_NAME_PARAM_NAME) +
            colon_literal_suppressed +
            param_type(RESULT_NAME_PARAM_TYPE))

        abc_name =  pyparsing.Word(pyparsing.alphas)

        semicolon_literal = pyparsing.Literal(";")

        zero_or_more_params = pyparsing.ZeroOrMore(param_listing(F"{RESULT_NAME_PARAMS}*"))
        final_expression_key = class_name(RESULT_NAME_CLASS_NAME)


        def _setLineAndLineNoAction(s:str, loc:int, toks:pyparsing.ParseResults) -> pyparsing.ParseResults:
            '''
            helper that gets called whenever a match for each line of the Telegram TL file gets hit, we
            add some entries to the 'parse results', which include the line number and original line text


            @param s is the original parse string
            @param loc is the location in the string where matching started
            @param toks is the list of the matched tokens, packaged as a ParseResults object
            @return a ParseResults if you are modifying it, else None
            '''

            t = toks
            orig_line = pyparsing.line(loc, s)
            orig_line_number = pyparsing.lineno(loc, s)

            logger.debug("loc: `%s`, lineno: `%s`, line: `%s`", loc, orig_line_number, orig_line)

            t[RESULT_NAME_SOURCE_LINE] = orig_line

            return t

        def _get_complete_expression(name_for_expression_after_equal:str) -> pyparsing.ParserElement:
            ''' helper that returns the same pyparsing expression but with a different 'name'
            for the part after the equal sign

            for types, the part after the `=` is the abstract class that the type extends

            for functions, the part after the `=` is the result type
            '''
            full_line = zero_or_more_params + \
                equal_sign_literal + \
                abc_name(name_for_expression_after_equal) + \
                semicolon_literal

            full_line.setParseAction(_setLineAndLineNoAction)

            final_expression_value =  full_line + \
                pyparsing.restOfLine

            # if i use pyparsing.ZeroOrMore instead of dictOf here, then it
            # basically smashes everything together into 1 entry
            to_return = pyparsing.dictOf(final_expression_key, final_expression_value)

            # ignore comments
            to_return.ignore(comment)

            return to_return

        # since the types come firs,t we need to see if we are skipping any lines or not
        complete_expression_for_tl_types =  _get_complete_expression(RESULT_NAME_EXTENDS_FROM_ABC)
        if skip_n_lines > 0:
            complete_expression_for_tl_types = skip_line * skip_n_lines + complete_expression_for_tl_types

            logger.debug("skip_n_lines is `%s`, adding `%s` SkipTo (`%s`) ParserElements to the expression",
                skip_n_lines, skip_n_lines, skip_line)

        logger.debug("final pyparsing expression for types: `%s`", complete_expression_for_tl_types)
        complete_expression_for_tl_functions = _get_complete_expression(RESULT_NAME_RETURN_TYPE)

        logger.debug("final pyparsing expression for functions: `%s`", complete_expression_for_tl_functions)

        if pyparsing_debug_logging_enabled:
            logger.debug("Turning on pyparsing debug logging")
            utils.setLoggingDebugActionForParserElement(complete_expression_for_tl_types)
            utils.setLoggingDebugActionForParserElement(complete_expression_for_tl_functions)


        res_types = None
        res_functions = None
        with open(tl_file_path, "r", encoding="utf-8") as f:

            full_file = f.read()

            tl_type_str, tl_functions_str = full_file.split("---functions---")

            res_types = complete_expression_for_tl_types.parseString(tl_type_str, parseAll=True)
            res_functions = complete_expression_for_tl_functions.parseString(tl_functions_str, parseAll=True)

        result_type_list = []
        result_fn_list = []

        # now convert the parse result to our own object

        # types:
        for iter_result in res_types.values():
            cls_name = iter_result[RESULT_NAME_CLASS_NAME]
            extends_from = iter_result[RESULT_NAME_EXTENDS_FROM_ABC]
            src_line = iter_result[RESULT_NAME_SOURCE_LINE]

            param_list = []


            if RESULT_NAME_PARAMS in iter_result.keys():
                for iter_param in iter_result[RESULT_NAME_PARAMS]:

                    p_name = iter_param[RESULT_NAME_PARAM_NAME]
                    p_type = iter_param[RESULT_NAME_PARAM_TYPE]

                    tlp = TlParameter(param_name=p_name, param_type=p_type)
                    logger.debug("--param: `%s`", tlp)
                    param_list.append(tlp)

            new_type = TlTypeDefinition(
                class_name=cls_name,
                params=param_list,
                inherits_from=extends_from,
                source_line=src_line)
            logging.debug("new type: `%s`", new_type)
            result_type_list.append(new_type)

        # functions:
        for iter_result in res_functions.values():
            cls_name = iter_result[RESULT_NAME_CLASS_NAME]
            rtn_type = iter_result[RESULT_NAME_RETURN_TYPE]

            src_line = iter_result[RESULT_NAME_SOURCE_LINE]
            param_list = []

            if RESULT_NAME_PARAMS in iter_result.keys():
                for iter_param in iter_result[RESULT_NAME_PARAMS]:

                    p_name = iter_param[RESULT_NAME_PARAM_NAME]
                    p_type = iter_param[RESULT_NAME_PARAM_TYPE]

                    tlp = TlParameter(param_name=p_name, param_type=p_type)
                    logger.debug("--param: `%s`", tlp)
                    param_list.append(tlp)


            new_fn = TlFunctionDefinition(
                class_name=cls_name,
                params=param_list,
                return_type=rtn_type,
                source_line=src_line)
            logging.debug("new function: `%s`", new_type)
            result_fn_list.append(new_fn)

        # create the final file definition
        result_file_def = TlFileDefinition(types=result_type_list, functions=result_fn_list)

        logging.debug("final parsed file definition: `%s` types and `%s` functions",
            len(result_file_def.types), len(result_file_def.functions))

        return result_file_def










