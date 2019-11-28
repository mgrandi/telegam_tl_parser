import json
import typing
import decimal
import io
import logging

import attr

from telegram_tl_parser.model import TlParameter, TlTypeDefinition, TlFunctionDefinition, TlFileDefinition, TlClassTypeEnum


logger = logging.getLogger(__name__)

class Generator:

    VERSION = 1

    INDENTATION = 4

    # these are the types that are usually lines 1-14 in the Telegram TL file, and can be replaced straight up
    # note: this does not include vector, which is handled specially below
    BASIC_TYPES_REPLACEMENT_DICT = {
        "double": "decimal.Decimal" ,
        "string": "str",
        "int32": "int",
        "int53": "int",
        "int64": "int",
        "bytes": "bytes",
        "Bool": "bool"}

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
        if obj.class_name == "TlRootObject":
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


    def tl_file_definition_to_attrs_classes(self, filedef:TlFileDefinition) -> str:
        '''
        takes a TlFileDefinition and converts it to Attrs style classes

        @param filedef a TlFileDefinition object
        @return a string containing the text of the class, suitable for writing out as a .py file
        '''

        l = logger.getChild("attrs_gen")


        # where we will write the result while constructing it
        out = io.StringIO()

        out.write("import attrs\n")
        out.write("\n")

        l.debug("starting TlFileDefinition -> attrs classes generation")

        l.debug("starting on types")

        # need to sort the types so we don't have the classes defined in a invalid order
        sorted_type_defs_list = sorted(filedef.types, key=self._tl_type_definition_sorter)

        # types
        for iter_type_def in sorted_type_defs_list:
            l.debug("current type def: `%s`", iter_type_def)
            out.write("@attr.s(auto_attribs=True, frozen=True)\n")

            # see if this class extends anything , everything should extend something except for the
            # "root object" we have
            if iter_type_def.extends_from:
                out.write(f"class {iter_type_def.class_name}({iter_type_def.extends_from}):\n")
            else:
                out.write(f"class {iter_type_def.class_name}:\n")

            # write out the parameters, or pass if there are none
            if len(iter_type_def.params) > 0:
                for iter_param_def in iter_type_def.params:
                    l.debug("-- param: `%s`", iter_param_def)

                    param_type = iter_param_def.param_type

                    # if its a type that has a replacement, replace it
                    if param_type in Generator.BASIC_TYPES_REPLACEMENT_DICT.keys():
                        l.debug("---- replacing `%s` with `%s`", param_type, Generator.BASIC_TYPES_REPLACEMENT_DICT[param_type])
                        param_type = Generator.BASIC_TYPES_REPLACEMENT_DICT[param_type]

                    out.write(f"{self._spaces(Generator.INDENTATION)}{iter_param_def.param_name}:{param_type} = attr.ib()\n")
            else:
                l.debug(" -- no parameters")
                out.write(f"{self._spaces(Generator.INDENTATION)}pass\n")

            out.write("\n")
            out.write("\n")

        # functions
        for iter_function_def in filedef.functions:
            l.debug("current function def: `%s`", iter_function_def)

            params_str_list = []

            for iter_param_def in iter_function_def.params:
                l.debug("-- param: `%s`", iter_param_def)
                iter_p_str = f"{iter_param_def.param_name}:{iter_param_def.param_type}"
                params_str_list.append(iter_p_str)
                l.debug("---- adding param string: `%s`", iter_p_str)

            params_string = ", ".join(params_str_list)
            out.write(f"def {iter_function_def.function_name}({params_string}) -> {iter_function_def.return_type}:\n")
            out.write(f"{self._spaces(Generator.INDENTATION)}pass")

            out.write("\n")
            out.write("\n")

        return out.getvalue()