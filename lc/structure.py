from __future__ import annotations

from typing import override

from lc.lexer import Token


class EvalContext:
    """Object to contain data used during interpretation."""
    def __init__(self):
        self.bound: dict[str, Expression] = {}  # map of bound variables
        self.eval_ops = True  # evaluate binary operations

        # force evaluation; difference between erroring, or returning self on failure
        self.force_eval = True

        self.eval_step = False  # evaluate one step


class Expression:
    """Describe a generic expression; something which can be evaluated."""
    def __init__(self, token: Token):
        self.token = token

    def substitute(self, old: str, new: Expression) -> Expression:
        """Substitute `old` with the given expression."""
        return self

    def substitute_argument(self, value: Expression) -> Expression:
        """Substitute an argument with `value`."""
        return self

    def evaluate(self, _ctx: EvalContext) -> Expression:
        """Evaluate expression to ground as much as possible."""
        raise NotImplemented

    def apply_argument(self, argument: Expression) -> Application:
        """Apply an argument to this expression."""
        return Application(self.token, self, argument)


def bracket_str(e: Expression):
    string = str(e)

    if isinstance(e, (Integer, Variable, Argument)):
        return string

    return string if string[0] == '(' else '(' + string + ')'


class Integer(Expression):
    """Represents an integer."""
    def __init__(self, token: Token, value: int | None = None):
        super().__init__(token)
        self.value = int(token.source) if value is None else value

    def __str__(self):
        return str(self.value)

    @override
    def evaluate(self, _ctx):
        return self


class Variable(Expression):
    """Describe a variable (this is *not* the same as an argument)."""
    def __str__(self):
        return self.token.source

    @override
    def evaluate(self, ctx):
        if (symbol := str(self)) in ctx.bound:
            return ctx.bound[symbol]

        if ctx.force_eval:
            raise NameError(f'{self.token.location()}: cannot evaluate unbound variable \'{symbol}\'')

        return self


class Argument(Expression):
    def __str__(self):
        return self.token.source

    @override
    def substitute(self, old, new):
        return new if self.token.source == old else self

    @override
    def evaluate(self, _ctx):
        return self


class BinaryOperation(Expression):
    def __init__(self, token: Token, lhs: Expression, rhs: Expression):
        super().__init__(token)
        self.lhs = lhs
        self.op = token.source
        self.rhs = rhs

    def __str__(self):
        return f'{bracket_str(self.lhs)} {self.op} {bracket_str(self.rhs)}'

    @override
    def substitute(self, old, new):
        return BinaryOperation(
            self.token,
            self.lhs.substitute(old, new),
            self.rhs.substitute(old, new)
        )

    @override
    def substitute_argument(self, value):
        return BinaryOperation(
            self.token,
            self.lhs.substitute_argument(value),
            self.rhs.substitute_argument(value)
        )

    @override
    def evaluate(self, ctx):
        new_lhs = self.lhs if ctx.eval_step else self.lhs.evaluate(ctx)
        new_rhs = self.rhs if ctx.eval_step else self.rhs.evaluate(ctx)

        if not ctx.eval_ops:
            return BinaryOperation(self.token, new_lhs, new_rhs)

        if self.op == '+':
            if isinstance(new_lhs, Integer) and isinstance(new_rhs, Integer):
                return Integer(self.token, new_lhs.value + new_rhs.value)

        if ctx.force_eval:
            raise TypeError(f'{self.token.location()}: unsupported arguments for operator \'{self.op}\': '
                            f'{new_lhs} {self.op} {new_rhs}')

        return BinaryOperation(self.token, new_lhs, new_rhs)


class Function(Expression):
    """Describes a one-argument function."""
    def __init__(self, token: Token, argument: Argument, body: Expression):
        super().__init__(token)
        self.argument = argument
        self.body = body

    @override
    def substitute(self, old, new):
        # our argument takes precedence over `old`
        if old == str(self.argument):
            return self

        return Function(
            self.token,
            self.argument,
            self.body.substitute(old, new)
        )

    @override
    def substitute_argument(self, value):
        # we have encountered an argument
        return self.body.substitute(str(self.argument), value)

    @override
    def evaluate(self, ctx):
        return self

    def __str__(self):
        return f'(\\{self.argument}. {self.body})'


class Application(Expression):
    def __init__(self, token: Token, target: Expression, value: Expression):
        super().__init__(token)
        self.target = target
        self.value = value

    @override
    def substitute(self, old, new):
        return Application(
            self.token,
            self.target.substitute(old, new),
            self.value.substitute(old, new)
        )

    @override
    def substitute_argument(self, value):
        return Application(
            self.token,
            self.target.substitute_argument(value),
            self.value.substitute_argument(value)
        )

    @override
    def evaluate(self, ctx):
        new_target = self.target if ctx.eval_step else self.target.evaluate(ctx)
        new_value = self.value if ctx.eval_step else self.value.evaluate(ctx)

        if isinstance(new_target, Function):
            result = new_target.substitute_argument(new_value)
            return result if ctx.eval_step else result.evaluate(ctx)

        if ctx.force_eval:
            raise ValueError(
                f'{self.token.location()}: {new_target} is not applicable (attempted to apply {new_value})')

        return Application(self.token, new_target, new_value)

    def __str__(self):
        return f'({bracket_str(self.target)} {bracket_str(self.value)})'
