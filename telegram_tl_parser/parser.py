import pathlib
import typing
import logging

import attr
import pyparsing

import telegram_tl_parser.utils as utils

logger = logging.getLogger(__name__)

@attr.s(auto_attribs=True, frozen=True)
class TlParameter:

    field_name:str = attr.ib()
    field_type:str = attr.ib()


@attr.s(auto_attribs=True, frozen=True)
class TlTypeDefinition:

    class_name:str = attr.ib()
    fields:typing.Sequence[TlParameter] = attr.ib()
    inherits_from:str = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlFunctionDefinition:

    class_name:str = attr.ib()
    fields:typing.Sequence[TlParameter] = attr.ib()
    return_type:str = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlFileDefinition:
    types:typing.Sequence[TlTypeDefinition] = attr.ib()
    functions:typing.Sequence[TlFunctionDefinition] = attr.ib()


class Parser:

    def __init__(self):

        pass

    def parse(self, tl_file_path:pathlib.Path, skip_n_lines:int) -> typing.Sequence[TlFileDefinition]:
        '''

        @param tl_file_path the Path to the .tl file we are parsing
        '''

        logger.info("parsing file: `%s`", tl_file_path)
        logger.info("skipping `%s` lines from the start of the file", skip_n_lines)

        # See `notes.md` for notes on the structure of the file

        skip_line = pyparsing.SkipTo(pyparsing.lineEnd, include=True)

        comment = pyparsing.Literal('//') - pyparsing.restOfLine

        class_name = pyparsing.Word(pyparsing.alphanums)
        equal_sign_literal = pyparsing.Literal("=")

        param_name = pyparsing.Word(pyparsing.alphanums + "_")
        colon_literal_suppressed = pyparsing.Literal(":").suppress()
        # need the angle brackets for stuff like `vector<String>`
        param_type =  pyparsing.Word(pyparsing.alphanums + "<>")

        ## dictOf(key,value) -> Dict(ZeroOrMore(Group(key + value)))
        param_listing = pyparsing.Group(param_name("param_name") +
            colon_literal_suppressed +
            param_type("param_type"))

        abc_name =  pyparsing.Word(pyparsing.alphas)

        semicolon_literal = pyparsing.Literal(";")


        def _get_complete_expression(name_for_expression_after_equal:str) -> pyparsing.ParserElement:
            ''' helper that returns the same pyparsing expression but with a differnet 'name'
            for the part after the equal sign

            for types, the part after the `=` is the abstract class that the type extends

            for functions, the part after the `=` is the result type
            '''

            # if i use pyparsing.ZeroOrMore instead of dictOf here, then it
            # basically smashes everything together into 1 entry
            to_return = pyparsing.dictOf(
                class_name("class_name*"), # key
                pyparsing.ZeroOrMore(param_listing)("params*") + # value
                    equal_sign_literal +
                    abc_name(name_for_expression_after_equal) +
                    semicolon_literal +
                    pyparsing.restOfLine)

            # ignore comments
            to_return.ignore(comment)

            return to_return

        # since the types come firs,t we need to see if we are skipping any lines or not
        complete_expression_for_tl_types =  _get_complete_expression("extends_from_abc")
        if skip_n_lines > 0:
            complete_expression_for_tl_types = skip_line * skip_n_lines + complete_expression_for_tl_types

            logger.debug("skip_n_lines is `%s`, adding `%s` SkipTo (`%s`) ParserElements to the expression",
                skip_n_lines, skip_n_lines, skip_line)

        utils.setLoggingDebugActionForParserElement(complete_expression_for_tl_types)
        logger.debug("final pyparsing expression for types: `%s`", complete_expression_for_tl_types)

        complete_expression_for_tl_functions = _get_complete_expression("return_type")
        utils.setLoggingDebugActionForParserElement(complete_expression_for_tl_functions)

        logger.debug("final pyparsing expression for functions: `%s`", complete_expression_for_tl_functions)


        res = None
        with open(tl_file_path, "r", encoding="utf-8") as f:

            full_file = f.read()

            tl_type_str, tl_functions_str = full_file.split("---functions---")

            res_types = complete_expression_for_tl_types.parseString(tl_type_str, parseAll=True)
            res_functions = complete_expression_for_tl_functions.parseString(tl_functions_str, parseAll=True)


            logging.debug("result for types is: `%s`", res_types.dump())
            logging.debug("result for functions is: `%s`", res_functions.dump())

        logging.info("done")







