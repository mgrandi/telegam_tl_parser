import json
import typing
import decimal
import io
import logging
import re

import attr

from telegram_tl_parser.model import TlParameter, TlTypeDefinition, TlFunctionDefinition, TlFileDefinition, TlClassTypeEnum
import telegram_tl_parser.constants as constants

logger = logging.getLogger(__name__)

class Generator:

    VERSION = 1

    INDENTATION = 4


    def _json_default(self, obj:typing.Any) -> typing.Any:
        '''
        method meant to be passed into `json.dumps(default=X)` to support
        custom types that can't be seralized by default

        @param obj the object that can't be serialized
        @return the serialized version of the object or we raise a TypeError if we can't handle it
        '''

        if isinstance(obj, TlClassTypeEnum):

            return obj.value
        else:

            raise TypeError(f"can't handle a object of type `{type(obj)}`")

    def tl_file_definition_to_json(self, filedef:TlFileDefinition) -> str:
        ''' takes a TlFileDefinition and converts it to JSON

        @param filedef a TlFileDefinition object
        @return a JSON string

        '''

        root_obj = {"__version__": Generator.VERSION, "tl_file_definition": {}}

        d = attr.asdict(filedef, recurse=True)

        root_obj["tl_file_definition"] = d

        json_str = json.dumps(root_obj, indent=4, default=self._json_default)

        return json_str

    def _tl_type_definition_sorter(self, obj:typing.Any) -> typing.Any:
        ''' function we pass to `sorted` to help us sort
        the list of types.

        since the types have to be in order (as in the class that is being extended needs to exist first)
        for python to load them properly, we apply that logic here and return either a 0, 1 or 2, depending on its
        priority

        note: we are returning a tuple, where the first element is the digit 0, 1, or 2, and the second element
        is just the class name, so it still sorts the way we want to but is more predictable i guess
        '''

        if not isinstance(obj, TlTypeDefinition):
            raise Exception(f"this sorting function only operates on TlTypeDefinition objects! got `{type(obj)}`")

        # option 1, it is the root object, it should go first before anything else
        if obj.class_name == constants.ROOT_OBJECT_NAME:
            return (0, obj.class_name)

        # option 2: where it is one of the abstract classes (other than the root object) , those should go
        # after the root object but before any of the concrete ones
        elif obj.class_type == TlClassTypeEnum.ABSTRACT:
           return (1, obj.class_name)

        # option 3: concrete classes, which go last
        else:

            return (2, obj.class_name)

    def _spaces(self, num_spaces:int) -> str:
        ''' helper that outputs the number of spaces we wwant

        @param num_spaces the number of spaces we want
        @return a string with X number of spaces
        '''

        return " " * num_spaces


    def _replace_basic_type_with_python_type(self, t:str) -> str:
        '''
        helper to look up in the Generator.BASIC_TYPES_REPLACEMENT_DICT dictionary
        '''
        if t in constants.BASIC_TYPES_REPLACEMENT_DICT.keys():
            replacement = constants.BASIC_TYPES_REPLACEMENT_DICT[t]
            logger.debug("------ replacing `%s` with `%s`", t, replacement)
            return replacement
        else:
            logger.debug("------ not replacing `%s` with anything, returning as is", t)
            return t

    def _pythonify_tl_type(self, tl_type:str) -> str:
        '''
        helper to take a object type that appears in a TL file and pythonify it

        aka `string` -> `str`
        `vector<string>` -> `typing.Sequence[str]`

        etc

        @param tl_type the TL type as a string that we read from the file
        @return the python-ified type to put in the class or function definition
        '''

        logger.debug("---- pythonifying the type `%s`", tl_type)
        result = None

        # first see if this is a vector type, as that requires special handling
        # if it is not a vector, just try and replace the type normally
        if (regex_result := constants.BASIC_TYPE_VECTOR_REGEX.search(tl_type)) is not None:

            logger.debug("------ vector regex matched: `%s`", regex_result)

            # it is a vector type, we need to loop becuase we could have arbitrarily nested vectors
            # since it already matched, we start out with 1 'sequence' wrapping the inner type, but
            # we might have double (or even triple? why) nested vectors
            running_prefix = "typing.Sequence["
            middle = regex_result.groupdict()[constants.BASIC_TYPE_VECTOR_REGEX_TYPE_NAME]
            running_suffix = "]"


            while True:
                logger.debug("-------- vector unwrapping, prefix: `%s`, middle: `%s`, suffix: `%s`",
                    running_prefix, middle, running_suffix)

                tmp_regex_result = constants.BASIC_TYPE_VECTOR_REGEX.search(middle)
                if tmp_regex_result:
                    logger.debug("---------- matched again")
                    running_prefix += "typing.Sequence["
                    running_suffix += "]"
                    middle = tmp_regex_result.groupdict()[constants.BASIC_TYPE_VECTOR_REGEX_TYPE_NAME]
                else:
                    logger.debug("---------- didn't match again")
                    break

            # replace the inner type, and then return it as prefix + middle (type) + suffix
            vector_inner_type = middle
            inner_type_replacement = self._replace_basic_type_with_python_type(vector_inner_type)

            result = f"{running_prefix}{inner_type_replacement}{running_suffix}"
        else:
            # it is not a vector type
            logger.debug("------ vector regex didn't match")
            result = self._replace_basic_type_with_python_type(tl_type)

        logger.debug("------ pythonify result: `%s` becomes `%s`", tl_type, result)
        return result


    def tl_file_definition_to_attrs_classes(self, filedef:TlFileDefinition) -> str:
        '''
        takes a TlFileDefinition and converts it to Attrs style classes

        @param filedef a TlFileDefinition object
        @return a string containing the text of the class, suitable for writing out as a .py file
        '''

        l = logger.getChild("attrs_gen")


        # where we will write the result while constructing it
        out = io.StringIO()

        # TODO: have this as a list instead of hardcoding it

        # you need this __future__ import or else you get errors if you have an annotation
        # for a class that doesn't yet exist
        # see https://www.python.org/dev/peps/pep-0563/ : "PEP 563 -- Postponed Evaluation of Annotations"
        out.write("from __future__ import annotations\n")
        out.write("import typing\n")
        out.write("import decimal\n")
        out.write("import json\n")
        out.write("\n")
        out.write("import attr\n")
        out.write("\n")
        out.write("\n")


        l.debug("starting TlFileDefinition -> attrs classes generation")

        l.debug("starting on types")

        # need to sort the types so we don't have the classes defined in a invalid order
        sorted_type_defs_list = sorted(filedef.types, key=self._tl_type_definition_sorter)

        # NOTE: you need `kw_only` or else you get errors because the root class has a parameter
        # with a default value while subclasses have parameters without a default value
        # see http://www.attrs.org/en/stable/examples.html#keyword-only-attributes
        attr_s_annotation_string = "@attr.s(auto_attribs=True, frozen=True, kw_only=True)\n"

        # types
        for iter_type_def in sorted_type_defs_list:
            l.debug("current type def: `%s`", iter_type_def)


            out.write(attr_s_annotation_string)

            # see if this class extends anything , everything should extend something except for the
            # "root object" we have
            if iter_type_def.extends_from:
                out.write(f"class {iter_type_def.class_name}({iter_type_def.extends_from}):\n")
            else:
                out.write(f"class {iter_type_def.class_name}:\n")

            # write out the special 'type' name
            out.write(f"{self._spaces(Generator.INDENTATION)}{constants.TDLIB_TYPE_VAR_NAME} = \"{iter_type_def.class_name}\"\n")

            # write out the parameters, or pass if there are none
            if len(iter_type_def.params) > 0:
                for iter_param_def in iter_type_def.params:
                    l.debug("-- param: `%s`", iter_param_def)

                    param_type = self._pythonify_tl_type(iter_param_def.param_type)

                    # handle if the parameter is marked as required or not
                    if iter_param_def.required:
                        out.write(f"{self._spaces(Generator.INDENTATION)}{iter_param_def.param_name}:{param_type} = attr.ib()\n")
                    else:
                        # special case string, where we need to surround the value in quotes
                        if isinstance(iter_param_def.default_value, str):
                            out.write(f"{self._spaces(Generator.INDENTATION)}{iter_param_def.param_name}:{param_type} = attr.ib(default=\"{iter_param_def.default_value}\")\n")
                        else:
                            out.write(f"{self._spaces(Generator.INDENTATION)}{iter_param_def.param_name}:{param_type} = attr.ib(default={iter_param_def.default_value})\n")



            else:
                l.debug(" -- no parameters")

            if iter_type_def.class_name == constants.ROOT_OBJECT_NAME:

                # create the special function for serializing the object as JSON
                out.write(f'''{self._spaces(Generator.INDENTATION)}def as_tdlib_json(self) -> str:\n''')
                out.write(f'''{self._spaces(Generator.INDENTATION * 2)}asdict_result = attr.asdict(self, filter=attr.filters.exclude(attr.fields({iter_type_def.class_name})._extra))\n''')
                out.write(f'''{self._spaces(Generator.INDENTATION * 2)}asdict_result["{constants.AS_TDLIB_JSON_TYPE_KEY_NAME}"] = self.{constants.TDLIB_TYPE_VAR_NAME}\n''')
                out.write(f'''{self._spaces(Generator.INDENTATION * 2)}if self._extra:\n''')
                out.write(f'''{self._spaces(Generator.INDENTATION * 3)}asdict_result["{constants.AS_TDLIB_JSON_EXTRA_KEY_NAME}"] = self._extra\n''')
                out.write(f'''{self._spaces(Generator.INDENTATION * 2)}return json.dumps(asdict_result)\n''')


            out.write("\n")
            out.write("\n")

        # functions
        for iter_function_def in filedef.functions:
            l.debug("current function def: `%s`", iter_function_def)


            out.write(attr_s_annotation_string)

            # all functions extend from 'root object'
            out.write(f"class {iter_function_def.function_name}({constants.ROOT_OBJECT_NAME}):\n")

            # write out the special 'type' name
            out.write(f"{self._spaces(Generator.INDENTATION)}{constants.TDLIB_TYPE_VAR_NAME} = \"{iter_function_def.function_name}\"\n")

            # write out the parameters, or pass if there are none
            if len(iter_function_def.params) > 0:
                for iter_param_def in iter_function_def.params:
                    l.debug("-- param: `%s`", iter_param_def)

                    param_type = self._pythonify_tl_type(iter_param_def.param_type)

                    out.write(f"{self._spaces(Generator.INDENTATION)}{iter_param_def.param_name}:{param_type} = attr.ib()\n")
            else:
                l.debug(" -- no parameters")

            out.write("\n")
            out.write("\n")


        return out.getvalue()