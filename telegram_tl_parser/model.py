from __future__ import annotations

import typing

import attr
import enum

class TlFileLineType(enum.Enum):
    '''
    describes the two types of lines, either
    a comment or a line defining a type or function
    '''
    COMMENT = "comment"
    DEFINITION = "definition"

class TlClassTypeEnum(enum.Enum):
    ''' describes the `types` that the TL file has

    some are listed explicitly, so they are concrete, and others are implied
    by what the concrete types extend
    '''

    CONCRETE = "concrete"
    ABSTRACT = "abstract"

class TlFileSectionType(enum.Enum):
    ''' describes the sections of the TL file
    '''
    TYPES = "types"
    FUNCTIONS = "functions"

@attr.s(auto_attribs=True, frozen=True)
class TlParameter:
    '''
    describes a parameter to either a type or function
    '''

    param_name:str = attr.ib()
    param_type:str = attr.ib()

    # as of right now, only TlRootObject makes use of these
    required:bool = attr.ib(default=True)
    default_value:typing.Any = attr.ib(default=None)

@attr.s(auto_attribs=True, frozen=True)
class TlTypeDefinition:
    '''
    describes a description of a type defined in the TL file
    '''

    class_name:str = attr.ib()
    parameters:typing.Sequence[TlParameter] = attr.ib()
    extends_from:typing.Optional[str] = attr.ib()
    source_line:str = attr.ib()
    source_line_number:int = attr.ib()
    class_type:TlClassTypeEnum = attr.ib()
    comments:typing.Sequence[TlComment] = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlFunctionDefinition:
    '''
    describes a description of a function defined in the TL file
    '''

    function_name:str = attr.ib()
    parameters:typing.Sequence[TlParameter] = attr.ib()
    return_type:str = attr.ib()
    source_line:str = attr.ib()
    source_line_number:int = attr.ib()
    comments:typing.sequence[TlComment] = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlComment:
    '''
    describes a comment in the TL file
    '''
    comment_text:str = attr.ib()
    source_line_number:str = attr.ib()

@attr.s(auto_attribs=True, frozen=True)
class TlFileDefinition:
    '''
    describes the definition of the entire TL file after parsing
    '''

    types:typing.Sequence[TlTypeDefinition] = attr.ib()
    functions:typing.Sequence[TlFunctionDefinition] = attr.ib()
