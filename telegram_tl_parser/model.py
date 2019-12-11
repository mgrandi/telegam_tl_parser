import typing

import attr
import enum

class TlClassTypeEnum(enum.Enum):
    CONCRETE = "concrete"
    ABSTRACT = "abstract"

@attr.s(auto_attribs=True, frozen=True)
class TlParameter:

    param_name:str = attr.ib()
    param_type:str = attr.ib()

    # as of right now, only TlRootObject makes use of these
    required:bool = attr.ib(default=True)
    default_value:typing.Any = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class TlTypeDefinition:

    class_name:str = attr.ib()
    params:typing.Sequence[TlParameter] = attr.ib()
    extends_from:typing.Optional[str] = attr.ib()
    source_line:str = attr.ib()
    class_type:TlClassTypeEnum = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlFunctionDefinition:

    function_name:str = attr.ib()
    params:typing.Sequence[TlParameter] = attr.ib()
    return_type:str = attr.ib()
    source_line:str = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlFileDefinition:

    types:typing.Sequence[TlTypeDefinition] = attr.ib()
    functions:typing.Sequence[TlFunctionDefinition] = attr.ib()
