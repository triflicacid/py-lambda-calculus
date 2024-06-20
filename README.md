# Lambda Calculus

This is a simple and exploratory lambda calculus-inspired interpreter.

# Execution

```
./run.py <filename> [options]
```

The following options are available:

- `--output-raw` - output each statement pre-evaluation.
- `--no-force-eval` - do not force evaluation (still evaluates where possible).
- `--no-eval-ops` - skip evaluation of operators.
- `--eval-step` - evaluate in steps, rather than in one go. If present, the raw statement will be output as well.

# Syntax

Atoms are the simplest of expressions and cannot be decomposed further.

- *Integers* are a sequence of digits.

Certain operators are also defined, as below.

- `+` defines integer addition.
- `-` defines integer subtraction.
- `*` define integer multiplication.
- `/` defines integer division (`floor(a / b)`).

Functions are the fundamental building-blocks of lambda calculus.
They take **one** argument and, on evaluation, substitutes this argument with the applied value.

```
\<arg>. <expr>
```

`<expr>` need not necessarily contain `<arg>`.


Expressions consist of atoms, expressions combined by operators, and functions.
If one expression follows another, the latter is "applied" to the former.
Note that this is immediate, and brackets must be used if more than an atom is wished to be supplied as the argument.
For example,

```
\x. x 2
(\x. x) 2
(\x. x) 2 + 1
(\x. x) (2 + 1)
```

1. This defines a function which, given `x`, applies `2` to `x`.
The output depends on the value of `x`.
2. This defines a function `\x. x` (identity), then passes `2` to it, outputting `2`.
3. Like above, we apply `2` to the identity function, then add `1`, outputting `3`.
4. Due to the bracket placement, this applies the entire expression `2 + 1` to identity, outputting `3` but in a different way.

When parsed, the file is scanned from start to end, everything assumed to be part of one large expression.
Semicolons may be used to start a new statement.
Comments, starting with `#`, may be included, and cause the rest of the line to be skipped.

Names may be bound with the following syntax:
```
<var> <- <expr>
```
During execution, any free-variable instances of `<var>` are evaluated to `<expr>`.
A name may only be assigned once.
