import re
from telegram_tl_parser.utils import strip_margin

ROOT_OBJECT_NAME = "RootObject"

TDLIB_TYPE_VAR_NAME = "__tdlib_type__"

AS_TDLIB_JSON_TYPE_KEY_NAME = "@type"
AS_TDLIB_JSON_EXTRA_KEY_NAME = "@extra"

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

BASIC_TYPE_VECTOR_REGEX_TYPE_NAME = "type"
BASIC_TYPE_VECTOR_REGEX = re.compile(f"^vector<(?P<{BASIC_TYPE_VECTOR_REGEX_TYPE_NAME}>.*)>$")

RESULT_NAME_SOURCE_LINE = "source_line"
RESULT_NAME_PARAMS = "params"
RESULT_NAME_PARAM_NAME = "param_name"
RESULT_NAME_PARAM_TYPE = "param_type"
RESULT_NAME_CLASS_OR_FUNCTION_NAME = "class_or_function_name"
RESULT_NAME_EXTENDS_FROM_ABC = "extends_from_abc"
RESULT_NAME_RETURN_TYPE = "return_type"


# you need this __future__ import or else you get errors if you have an annotation
# for a class that doesn't yet exist
# see https://www.python.org/dev/peps/pep-0563/ : "PEP 563 -- Postponed Evaluation of Annotations"
# also the future line needs to be on the first line of the file
ATTRS_GEN_IMPORT_STATEMENTS = \
'''from __future__ import annotations
import typing
import decimal

import attr

from telegram_dl import utils

'''

# NOTE: this is a method in a class so everything needs to be indented 4 spaces to start
ATTRS_GEN_AS_TDLIB_JSON = strip_margin(
    f'''
    |    def as_tdlib_json(self) -> str:
    |        return utils.custom_asdict(self, filter=attr.filters.exclude(attr.fields(RootObject)._extra))

    ''')