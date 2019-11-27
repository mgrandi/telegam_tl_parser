import json
import typing

import attr

from telegram_tl_parser.model import TlParameter, TlTypeDefinition, TlFunctionDefinition, TlFileDefinition, TlClassTypeEnum

class Generator:

    VERSION = 1

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

    def tl_file_definition_to_attrs_classes(self, filedef:TlFileDefinition) -> str:
        '''
        takes a TlFileDefinition and converts it to Attrs style classes

        @param filedef a TlFileDefinition object
        @return a string containing the text of the class, suitable for writing out as a .py file
        '''

        raise Exception("Not implemented yet")