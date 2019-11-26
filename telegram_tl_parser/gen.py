
import json

import attr

from telegram_tl_parser.model import TlParameter, TlTypeDefinition, TlFunctionDefinition, TlFileDefinition

class Generator:

    VERSION = 1


    def tl_file_definition_to_json(self, filedef:TlFileDefinition) -> str:
        ''' takes a TlFileDefinition and converts it to JSON

        @param filedef a TlFileDefinition object
        @return a JSON string

        '''

        root_obj = {"__version__": Generator.VERSION, "tl_file_definition": {}}


        d = attr.asdict(filedef, recurse=True)

        root_obj["tl_file_definition"] = d

        json_str = json.dumps(root_obj, indent=4)

        return json_str

    def tl_file_definition_to_attrs_classes(self, filedef:TlFileDefinition) -> str:
        '''
        takes a TlFileDefinition and converts it to Attrs style classes

        @param filedef a TlFileDefinition object
        @return a string containing the text of the class, suitable for writing out as a .py file
        '''

        raise Exception("Not implemented yet")