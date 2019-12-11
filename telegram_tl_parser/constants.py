import re

ROOT_OBJECT_NAME = "RootObject"

ATTRS_OUTPUT_TYPE_PREFIX = "tdlib_type_"
ATTRS_OUTPUT_FUNC_PREFIX = "tdlib_func_"

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

