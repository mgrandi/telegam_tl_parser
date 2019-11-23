# pyparsing notes

so it seems with pyparsing, if you want to fiddle how the final 'structure' according to `ParserElement.dump()` looks / acts, you
need to fiddle with a few things

* pyparsing.Group
* pyparsing.Optional
* pyparsing.ZeroOrMore/OneOrMore
* pyparsing.dictOf (which is really just `Dict(ZeroOrMore(Group(key + value)))`)
* `setResultName(<str>, True)` or the `__call__` syntax with an `*` at the end (aka, like `pyparsing.Word("hi")("test*"))`

for example, here is the line that i am parsing, and the pyparsing code for the tl file i have in parser.py, a bit simplified

line:

```plaintext
temporaryPasswordState has_password:Bool valid_for:int32 = TemporaryPasswordState;
```

and the pyparsing code, with markers (aka `[N]`)

```python
skip_line = pyparsing.SkipTo(pyparsing.lineEnd, include=True)

comment = pyparsing.Literal('//') - pyparsing.restOfLine

class_name = pyparsing.Word(pyparsing.alphanums)
equal_sign_literal = pyparsing.Literal("=")

param_name = pyparsing.Word(pyparsing.alphanums + "_")
colon_literal_suppressed = pyparsing.Literal(":").suppress()
# need the angle brackets for stuff like `vector<String>`
param_type =  pyparsing.Word(pyparsing.alphanums + "<>")

param_listing = pyparsing.Group( # [1]
    param_name("param_name") +
    colon_literal_suppressed +
    param_type("param_type"))

abc_name =  pyparsing.Word(pyparsing.alphas)

semicolon_literal = pyparsing.Literal(";")


zero_or_more_params = pyparsing.ZeroOrMore(param_listing("params*")) # [2]
final_expression_key = class_name("class_name")
final_expression_value =  zero_or_more_params +
        equal_sign_literal +
        abc_name(name_for_expression_after_equal) +
        semicolon_literal +
        pyparsing.restOfLine

final_expression = pyparsing.dictOf(final_expression_key, final_expression_value)


```

The code above, when run, generates this when you call `final_expression.parseString(<somestr>).dump()`:

```plaintext
- temporaryPasswordState: [['has_password', 'Bool'], ['valid_for', 'int32'], '=', 'TemporaryPasswordState', ';', '']
  - class_name: 'temporaryPasswordState'
  - extends_from_abc: 'TemporaryPasswordState'
  - params: [['has_password', 'Bool'], ['valid_for', 'int32']]
    [0]:
      ['has_password', 'Bool']
      - param_name: 'has_password'
      - param_type: 'Bool'
    [1]:
      ['valid_for', 'int32']
      - param_name: 'valid_for'
      - param_type: 'int32'`
```

But if i change the pyparsing code a bit:

```python

# change code at marker `[1]` to be `pyparsing.dictOf` instead of `pyparsing.Group`
param_listing = pyparsing.dictOf( # [1]
    param_name("param_name"),
    colon_literal_suppressed +
    param_type("param_type"))

# and then change the 'zero_or_more_params' expression at mark `[2]`to not have a `*`
# when doing the setResultsName call:

zero_or_more_params = pyparsing.ZeroOrMore(param_listing("params")) # [2]


```

then you get this result, with the params not being part of a list, but instead the `param_name` being the key and
`param_value` being the value for a dictionary

```plaintext
- temporaryPasswordState: [[['has_password', 'Bool'], ['valid_for', 'int32']], '=', 'TemporaryPasswordState', ';', '']
  - class_name: 'temporaryPasswordState'
  - extends_from_abc: 'TemporaryPasswordState'
  - params: [['has_password', 'Bool'], ['valid_for', 'int32']]
    - has_password: 'Bool'
    - valid_for: 'int32'`

```

basing off the code we just changed, if we change this:

```python

# change the `setResultsName` call to have an `*` after all
zero_or_more_params = pyparsing.ZeroOrMore(param_listing("params*")) # [2]

```


you get this, where the params are still in a dictionary, but the dictionary itself is inside a list.

```plaintext

- temporaryPasswordState: [[['has_password', 'Bool'], ['valid_for', 'int32']], '=', 'TemporaryPasswordState', ';', '']
  - class_name: 'temporaryPasswordState'
  - extends_from_abc: 'TemporaryPasswordState'
  - params: [[['has_password', 'Bool'], ['valid_for', 'int32']]]
    [0]:
      [['has_password', 'Bool'], ['valid_for', 'int32']]
      - has_password: 'Bool'
      - valid_for: 'int32'`
```


This is just to show how changing various things can impact the final structure of the ParseResults.

