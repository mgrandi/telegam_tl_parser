# tl scheme notes

## overview

A `Telegram TL` file is a file with 1 "definition" per line. A line can either start with a comment (`//`) or it can contain a definition

the type of 'definition' depends on where in the file you are, see `sections`. A `Telegram TL` file usually has 2
sections, the first section will have 'type definitions', and will start from the beginning of the file until you reach
the string `---functions---`. After that, you have 'function definitions'

Note: the first 14 lines of the `Telegram tdlib TL` file that [Telegram distributes here](https://github.com/tdlib/td/blob/master/td/generate/scheme/td_api.tl) can be safely ignored, see [here](https://github.com/tdlib/td/issues/735#issuecomment-544156906).

Example:

```plaintext
authenticationCodeTypeCall length:int32 = AuthenticationCodeType;
temporaryPasswordState has_password:Bool valid_for:int32 = TemporaryPasswordState;
ok = Ok;

---functions---

getAuthorizationState = AuthorizationState;
setTdlibParameters parameters:tdlibParameters = Ok;
setAuthenticationPhoneNumber phone_number:string settings:phoneNumberAuthenticationSettings = Ok;
```

`tdlib` basically only exposes a few functions, all of which deal with JSON. All of the types defined in the `Telegram TL` file
are converted directly to JSON and sent as parameters (or returned as a return type) when you call a function or get an event from `tdlib`. When you use `td_send()`, you use `@type` to specify what api you are calling, and when telegram sends you an event with `td_receive()`, `@type` is the Type of the event. After that, everything directly translates to JSON.

Example from tdlib's [`example.py`](https://github.com/tdlib/td/blob/9293f07464276d58974164e41a4bb57d3362a258/example/python/tdjson_example.py), which is calling the `setTdlibParameters` function with a `tdlibParameters` object.

```python3
# set TDLib parameters
# you MUST obtain your own api_id and api_hash at https://my.telegram.org
# and use them in the setTdlibParameters call
if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
    td_send({'@type': 'setTdlibParameters', 'parameters': {
                                           'database_directory': 'tdlib',
                                           'use_message_database': True,
                                           'use_secret_chats': True,
                                           'api_id': 94575,
                                           'api_hash': 'a3406de8d171bb422bb6ddf3bbd800e2',
                                           'system_language_code': 'en',
                                           'device_model': 'Desktop',
                                           'system_version': 'Linux',
                                           'application_version': '1.0',
                                           'enable_storage_optimizer': True}})
```



## sections


### types

basic syntax:

```plaintext
className paramName:paramType = InheritsFromAbstractType;
```

example:

```plaintext
authenticationCodeTypeCall length:int32 = AuthenticationCodeType;
temporaryPasswordState has_password:Bool valid_for:int32 = TemporaryPasswordState;
ok = Ok;
```

if these were converted to a python class using `attrs`, it would look like:

```plaintext
@attr.s
class AuthenticationCodeType:
    # some definition here

@attr.s
class TemporaryPasswordState:
    # some definition here

@attr.s
class Ok:
    pass # no parameters


@attr.s
class ok(OK):
    pass


@attr.s
class authenticationCodeTypeTelegramMessage(AuthenticationCodeType):
    length:int = attr.ib()

@attr.s
class temporaryPasswordState(TemporaryPasswordState):
    has_password:bool = attr.ib()
    valid_for:int = attr.ib()

```



### functions

very similiar to 'types', but with one difference, the thing after the equal sign is the return type

```plaintext
methodName paramName:paramType = ReturnType;
```

example:

```plaintext
// a comment here
getAuthorizationState = AuthorizationState;
setTdlibParameters parameters:tdlibParameters = Ok;
setAuthenticationPhoneNumber phone_number:string settings:phoneNumberAuthenticationSettings = Ok;
```

if converted to a python class using `attrs`, it would look like:

```plaintext

@attr.s
class AuthorizationState:
    # some definition here

@attr.s
class tdlibParameters:
    # some definition here

@attr.s
class phoneNumberAuthenticationSettings:
    # some definition here

def getAuthorizationState() -> AuthorizationState:
    # some definition here

def setTdlibParameters(parameters:tdlibParameters) -> Ok:
    # some definition here

def setAuthenticationPhoneNumber(phone_number:str, settings:phoneNumberAuthenticationSettings) -> Ok:
    # some definition here

```

## misc

there are different schemas for telegram , TDLib, and others

### TL "language"
https://core.telegram.org/mtproto/TL

### schema for normal telegram
https://core.telegram.org/schema
https://core.telegram.org/schema/json


### schema for TDLib

https://github.com/tdlib/td/blob/master/td/generate/scheme/td_api.tl

actual useful description
https://github.com/tdlib/td/issues/735#issuecomment-544152952

```
@dancojocaru2000

The TL subset used for TDLib API is very simple.
A simple object declaration

error code:int32 message:string = Error;

describes a type with its fields. The type name here is error and it is inherited from an abstract type Error.

Some abstract types can have more than one inheritor. For example, in

textParseModeMarkdown = TextParseMode;
textParseModeHTML = TextParseMode;

described that type TextParseMode can be one of textParseModeMarkdown or textParseModeHTML. Abstract class names always begins with a capital letter and ordinary classes always begins with a lowercase letter.

There is also a ---functions--- section, which describes all TDLib API methods. Declarations there are different only in one thing: they contain method's result type after = instead of the inherited abstract class. For example, the method

parseTextEntities text:string parse_mode:TextParseMode = FormattedText;

has string argument text, the argument parameters of an abstract type TextParseMode and returns an object of type FormattedText. The latter is an abstract type with one constructor formattedText, so the result always will be of the type formattedText.

That's all. But we didn't expect that even this is needed to be known and have auto-generated documentation for C++, Java and C# interfaces. There are a lot of third-party wrappers which also provide auto-generated documentation in a usual form for other programming languages.
```
