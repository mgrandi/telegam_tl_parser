import pathlib
import typing
import logging

import attr
import pyparsing

import telegram_tl_parser.utils as utils
import telegram_tl_parser.constants as constants
import  telegram_tl_parser.model as model

logger = logging.getLogger(__name__)

class Parser:

    def __init__(self):
        '''
        See `notes.md` for notes on the structure of the file
        and see `pyparsing_notes.md` for notes on pyparsing stuff

        example full lines we are parsing:

        getJsonValue json:string = JsonValue;

        setPollAnswer chat_id:int53 message_id:int53 option_ids:vector<int32> = Ok;

        getInlineQueryResults bot_user_id:int32 chat_id:int53 user_location:location query:string offset:string = InlineQueryResults;
        '''

        # a literal newline
        self.pe_newline = pyparsing.Literal('\n')

        # a semicolon literal
        self.pe_semicolon_literal = pyparsing.Literal(";")

        # a literal colon
        self.pe_colon_literal = pyparsing.Literal(":")

        # literal equal sign
        self.pe_equal_sign_literal = pyparsing.Literal("=")

        # a literal for the start of a comment
        self.pe_comment_literal = pyparsing.Literal('//')

        # token that skips to the end of a line
        # used for the program argument to skip 'N' number of lines
        self.pe_skip_line = pyparsing.SkipTo(pyparsing.lineEnd, include=True)

        # words that can appear in a class name
        self.pe_class_name = pyparsing.Word(pyparsing.alphanums)

        # characters that appear in a parameter name or type
        self.pe_param_name = pyparsing.Word(pyparsing.alphanums + "_")

        # need the angle brackets for stuff like `vector<String>`
        self.pe_param_type =  pyparsing.Word(pyparsing.alphanums + "<>")

        # a single param and type pair
        # so like `message:string`
        self.pe_param_listing = pyparsing.Group(
            self.pe_param_name(constants.RESULT_NAME_PARAM_NAME) +
            self.pe_colon_literal.suppress() +
            self.pe_param_type(constants.RESULT_NAME_PARAM_TYPE))

        # grouping of zero or more parameters
        self.pe_zero_or_more_params = pyparsing.ZeroOrMore(
            self.pe_param_listing(f"{constants.RESULT_NAME_PARAMS}*"))

        # the actual name of the class/type that is being defined
        self.pe_tdlib_class_name = self.pe_class_name(constants.RESULT_NAME_CLASS_OR_FUNCTION_NAME)




    def _setLineAndLineNumberParseAction(self, s:str, loc:int, toks:pyparsing.ParseResults) -> pyparsing.ParseResults:
        '''
        helper that is meant to be used with `<ParserElement>.setParseAction`, which means this function gets called
        whenever a match for each line of the Telegram TL file gets hit.

        Here we add stuff to the ParseResults that it passes in

        we add the source line and source line number to each match

        @param s is the original parse string
        @param loc is the location in the string where matching started
        @param toks is the list of the matched tokens, packaged as a ParseResults object
        @return a ParseResults if you are modifying it, else None
        '''

        t = toks
        orig_line = pyparsing.line(loc, s)
        line_number = pyparsing.lineno(loc, s)
        column = pyparsing.col(loc, s)

        logger.debug("_setLineAndLineNumberParseAction: line_number: `%s`, column: `%s`,  line: `%s`",
            line_number, column, orig_line)

        t[constants.RESULT_NAME_SOURCE_LINE] = orig_line
        t[constants.RESULT_NAME_SOURCE_LINE_NUMBER] = line_number

        return t


    def _setTlLineTypeStringParseAction(self, line_type:model.TlFileLineType) -> typing.Callable[[str,int,pyparsing.ParseResults], pyparsing.ParseResults]:
        '''
        return _inner which will be the function actually called by pyparsing when it encounters a match
        but it will 'capture' the `line_type` param and be able to use that to add to the token dictionary
        on a match

        should be registered using .setParseAction on the pyparsing.ParserElement that is responsible
        for matching the given `TlFileLineType`

        @param line_type the line type enum member identifying what this line is

        @return a function that can be registered as a parser action using `.setParseAction`
        '''

        def _inner( s:str, loc:int, toks:pyparsing.ParseResults) -> pyparsing.ParseResults:
            '''
            helper that is meant to be used with `<ParserElement>.setParseAction`, which means this function gets called
            whenever a match for each line of the Telegram TL file gets hit.

            Here we add stuff to the ParseResults that it passes in

            this will add a enum to the token dictionary if the match is a line or a comment

            @param s is the original parse string
            @param loc is the location in the string where matching started
            @param toks is the list of the matched tokens, packaged as a ParseResults object
            @return a ParseResults if you are modifying it, else None
            '''


            line_number = pyparsing.lineno(loc, s)
            column = pyparsing.col(loc, s)
            toks[constants.RESULT_NAME_TL_LINE_TYPE] = line_type
            logger.debug("_setTlLineTypeStringParseAction._inner: setting type to be `%s` at line num: `%s`, col: `%s`",
                line_type, line_number, column)
            return toks

        return _inner



    def _get_complete_expression(self, name_for_expression_after_equal:str) -> pyparsing.ParserElement:
        ''' helper that returns the same pyparsing expression but with a different 'name'
        for the part after the equal sign

        for types, the part after the `=` is the abstract class that the type extends

        for functions, the part after the `=` is the result type
        '''

        # everything in a line that is past the initial 'name' of the class/type that is being defined
        pe_params_list_equal_sign_and_extends_from = \
            self.pe_zero_or_more_params + \
            self.pe_equal_sign_literal.suppress() + \
            self.pe_class_name(name_for_expression_after_equal) + \
            self.pe_semicolon_literal

        # the full line definition for a line that is describing a tdlib type/class (aka not a comment)
        pe_full_line_tdlib_type_def = \
            self.pe_tdlib_class_name + \
            pe_params_list_equal_sign_and_extends_from

        # set parser action to add a 'note' that this is a `DEFINITION` line
        pe_full_line_tdlib_type_def.addParseAction(self._setTlLineTypeStringParseAction(model.TlFileLineType.DEFINITION))

        # set parser action to add the line and column numbers
        pe_full_line_tdlib_type_def.addParseAction(self._setLineAndLineNumberParseAction)


        pe_full_comment_line = \
            self.pe_comment_literal + \
            pyparsing.restOfLine(constants.RESULT_NAME_COMMENT_TEXT)

        # set parser action to add a 'note' that this is a `COMMENT` line
        pe_full_comment_line.addParseAction(self._setTlLineTypeStringParseAction(model.TlFileLineType.COMMENT))

        # set parser action to add the line and column numbers
        pe_full_comment_line.addParseAction(self._setLineAndLineNumberParseAction)

        to_return = \
            pyparsing.ZeroOrMore(
                pyparsing.Group(
                    pyparsing.Or(
                            [pe_full_line_tdlib_type_def,
                            pe_full_comment_line]
                        )
                    )
                )

        return to_return

    def parse(self,
        tl_file_path:pathlib.Path,
        skip_n_lines:int,
        pyparsing_debug_logging_enabled:bool) -> typing.Sequence[model.TlFileDefinition]:
        '''
        @param tl_file_path the Path to the .tl file we are parsing

        '''

        logger.info("parsing file: `%s`", tl_file_path)
        logger.info("skipping `%s` lines from the start of the file", skip_n_lines)


        pe_complete_expression_for_tl_types =  self._get_complete_expression(constants.RESULT_NAME_EXTENDS_FROM_ABC)

        # since the types come first, we need to see if we are skipping any lines or not
        if skip_n_lines > 0:

            # I did not need to add `suppress()` before , but for some reason now i do? strange...
            # if i don't add it then it 'skips' the lines but the lines that i 'skip' still end up
            # in the parsed results =/
            # maybe i got lucky with a previous commit's pattern where the first X lines wouldn't
            # match anyway even if they were 'accepted' by SkipTo? Cause the documentation for
            # `SkipTo` is `skips ahead in the input string, accepting any characters up`the specified pattern`
            # so that makes me think that i just got lucky and i actually always needed to add `suppress()`
            # to the `SkipTo` elements i added
            #
            # also: adding all of the `SkipTo` ParserElements to a group and then calling `suppress()`
            # on that makes the pattern shorter (for debugging), as there is only one `suppress()` and not
            # X for `skip_n_lines`
            skip_group = pyparsing.Group(self.pe_skip_line * skip_n_lines).suppress()
            pe_complete_expression_for_tl_types = skip_group + pe_complete_expression_for_tl_types

            logger.debug("skip_n_lines is `%s`, adding `%s` SkipTo (`%s`) ParserElements to the expression",
                skip_n_lines, skip_n_lines, self.pe_skip_line)

        logger.debug("final pyparsing expression for types: `%s`", pe_complete_expression_for_tl_types)

        # we don't need to skip any lines for functions since the only thing we skip are types
        pe_complete_expression_for_tl_functions = self._get_complete_expression(constants.RESULT_NAME_RETURN_TYPE)

        logger.debug("final pyparsing expression for functions: `%s`", pe_complete_expression_for_tl_functions)

        if pyparsing_debug_logging_enabled:
            logger.debug("Turning on pyparsing debug logging")
            utils.setLoggingDebugActionForParserElement(pe_complete_expression_for_tl_types)
            utils.setLoggingDebugActionForParserElement(pe_complete_expression_for_tl_functions)
            utils.setLoggingDebugActionForParserElement(self.pe_skip_line)


        parse_results_dict = dict()

        with open(tl_file_path, "r", encoding="utf-8") as f:

            full_file = f.read()

            tl_type_str, tl_functions_str = full_file.split("---functions---")

            res_types = pe_complete_expression_for_tl_types.parseString(tl_type_str, parseAll=True)
            parse_results_dict[model.TlFileSectionType.TYPES] = res_types

            res_functions = pe_complete_expression_for_tl_functions.parseString(tl_functions_str, parseAll=True)
            parse_results_dict[model.TlFileSectionType.FUNCTIONS] = res_functions


        all_tl_types_to_add_to_file_definition = []

        # now convert the parse result to our own object

        for iter_file_section_type, iter_parse_results in parse_results_dict.items():

            logger.debug("Processing results from `%s`", iter_file_section_type)

            # so how the 'results' work that we get back from pyparsing is that
            # they are in a giant list, so since the comments are ABOVE the
            # types and functions, we are going to go through each of the items
            # in the parse results, and if it is a `TlFileLineType.COMMENT`,
            # we create a TlComment and add it to this list, and then once we get
            # to a non comment (aka `TlFileLineType.TYPE`) we then consume all of
            # the items in this list and add it to the `TlTypeDefinition` or
            # `TlFunctionDefinition`
            queued_comments = list()

            for iter_result in iter_parse_results:

                line_type = iter_result[constants.RESULT_NAME_TL_LINE_TYPE]

                if line_type == model.TlFileLineType.COMMENT:

                    comment_text = iter_result[constants.RESULT_NAME_COMMENT_TEXT]
                    src_line_num = iter_result[constants.RESULT_NAME_SOURCE_LINE_NUMBER]

                    new_comment = model.TlComment(
                        comment_text=comment_text,
                        source_line_number = src_line_num)

                    queued_comments.append(new_comment)


                elif line_type == model.TlFileLineType.DEFINITION:

                    type_to_create = None

                    type_to_create_kwargs = dict()

                    # copy the currently queued comments and
                    # clear the 'queue'
                    comments = [x for x in queued_comments]
                    queued_comments = list()

                    # common parameters between TYPES and FUNCTIONS
                    src_line = iter_result[constants.RESULT_NAME_SOURCE_LINE]
                    src_line_num = iter_result[constants.RESULT_NAME_SOURCE_LINE_NUMBER]

                    type_to_create_kwargs["source_line"] = src_line
                    type_to_create_kwargs["source_line_number"] = src_line_num
                    type_to_create_kwargs["comments"] = comments

                    # get any parameters for this type or function if they exist
                    param_list = []
                    if constants.RESULT_NAME_PARAMS in iter_result.keys():
                        for iter_param in iter_result[constants.RESULT_NAME_PARAMS]:

                            p_name = iter_param[constants.RESULT_NAME_PARAM_NAME]
                            p_type = iter_param[constants.RESULT_NAME_PARAM_TYPE]

                            tlp = model.TlParameter(param_name=p_name, param_type=p_type)
                            logger.debug("--param: `%s`", tlp)
                            param_list.append(tlp)

                    type_to_create_kwargs["parameters"] = param_list

                    # specific arguments for either TYPES or FUNCTIONS

                    if iter_file_section_type == model.TlFileSectionType.TYPES:

                        type_to_create = model.TlTypeDefinition

                        cls_name = iter_result[constants.RESULT_NAME_CLASS_OR_FUNCTION_NAME]
                        extends_from = iter_result[constants.RESULT_NAME_EXTENDS_FROM_ABC]

                        type_to_create_kwargs["class_name"] = cls_name
                        type_to_create_kwargs["extends_from"] = extends_from
                        type_to_create_kwargs["class_type"] = model.TlClassTypeEnum.CONCRETE

                    elif iter_file_section_type == model.TlFileSectionType.FUNCTIONS:

                        type_to_create = model.TlFunctionDefinition

                        fn_name = iter_result[constants.RESULT_NAME_CLASS_OR_FUNCTION_NAME]
                        rtn_type = iter_result[constants.RESULT_NAME_RETURN_TYPE]

                        type_to_create_kwargs["function_name"] = fn_name
                        type_to_create_kwargs["return_type"] = rtn_type

                    else:

                        raise Exception(f"unhandled TlFileSectionType! type: `{iter_file_section_type}`")


                    # now create the specified type with the specified arguments and add it
                    # to our list

                    new_type = type_to_create(**type_to_create_kwargs)

                    logger.debug("added new `%s`: `%s`", type(new_type), new_type)

                    all_tl_types_to_add_to_file_definition.append(new_type)

                else:

                    raise Exception(f"Unhandled TlFileLineType! type: `{line_type}`")


        # sort the results into functions and types
        def _filter_by_type(the_list, the_type):
            return  [x for x in the_list if isinstance(x, the_type)]

        tl_concrete_types_to_add_to_file_definition = _filter_by_type(all_tl_types_to_add_to_file_definition, model.TlTypeDefinition)
        tl_funcs_to_add_to_file_definition = _filter_by_type(all_tl_types_to_add_to_file_definition, model.TlFunctionDefinition)


        # so here we have the 'explicit' results, but we need to create entries for the 'implicit' class types
        # for example, `authenticationCodeTypeTelegramMessage length:int32 = AuthenticationCodeType;` means that
        # the class `authenticationCodeTypeTelegramMessage` extends `AuthenticationCodeType`, but that class
        # is never explicitly defined in the TL file, so we need to make it

        # dict of the class name as a string -> TlTypeDefinition
        result_abstract_types_dict = dict()

        logger.debug("creating abstract type definitions")

        # first create the "root" object that all of the abstract classes will extend from
        root_type = model.TlTypeDefinition(
                class_name=constants.ROOT_OBJECT_NAME,
                parameters=[model.TlParameter(param_name="_extra", param_type="str", required=False, default_value="")],
                extends_from=None,
                source_line_number=-1,
                source_line = "",
                comments=[],
                class_type=model.TlClassTypeEnum.ABSTRACT)

        result_abstract_types_dict[root_type.class_name] = root_type

        # then go through and create more depending on the Concrete TlTypeDefinitions we created from the file
        for iter_type_def in tl_concrete_types_to_add_to_file_definition:
            iter_abstract_class_name = iter_type_def.extends_from

            if iter_abstract_class_name not in result_abstract_types_dict.keys():

                new_abstract_type = model.TlTypeDefinition(
                    class_name=iter_abstract_class_name,
                    parameters=[],
                    extends_from=root_type.class_name,
                    source_line_number=-1,
                    source_line = "",
                    comments=[],
                    class_type=model.TlClassTypeEnum.ABSTRACT)

                logger.debug("new abstract type definition: `%s`", new_abstract_type)
                result_abstract_types_dict[iter_abstract_class_name] = new_abstract_type

            else:

                logger.debug("abstract type was already created: `%s`", iter_abstract_class_name)

        # create the final file definition
        final_types_list = tl_concrete_types_to_add_to_file_definition + list(result_abstract_types_dict.values())

        result_file_def = model.TlFileDefinition(types=final_types_list, functions=tl_funcs_to_add_to_file_definition)

        logging.info("final parsed file definition: `%s` concrete types, `%s` abstract types and `%s` functions",
            len(tl_concrete_types_to_add_to_file_definition),
            len(result_abstract_types_dict.values()),
            len(result_file_def.functions))

        return result_file_def










