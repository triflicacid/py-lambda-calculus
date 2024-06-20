from __future__ import annotations

from typing import override

from lc.lexer import Token


class EvalContext:
    """Object to contain data used during interpretation."""
    def __init__(self):
        self.bound: dict[str, Expression] = {}  # map of bound variables
        self.eval_ops = True  # evaluate binary operations
        self.eval_step = False  # evaluate one step

        # force evaluation; difference between erroring, or returning self on failure
        self.force_eval = True


class Expression:
    """Describe a generic expression; something which can be evaluated."""
    def __init__(self, token: Token):
        self.token = token

    def substitute(self, old: str, new: Expression) -> Expression:
        """Substitute `old` with the given expression."""
        return self

    def is_atomic(self, ctx: EvalContext):
        """Return whether we are atomic (can be evaluated)."""
        raise NotImplemented

    def evaluate(self, ctx: EvalContext) -> Expression:
        """Evaluate expression to ground as much as possible."""
        raise NotImplemented

    def apply_argument(self, argument: Expression) -> Application:
        """Apply an argument to this expression."""
        return Application(self.token, self, argument)


def bracket_str(e: Expression):
    string = str(e)

    if isinstance(e, (Variable, Argument, List)) or (isinstance(e, Integer) and e.value >= 0):
        return string

    return string if string[0] == '(' else '(' + string + ')'


class Integer(Expression):
    """Represents an integer."""
    def __init__(self, token: Token, value: int | None = None):
        super().__init__(token)
        self.value = int(token.source) if value is None else value

    def __str__(self):
        return str(self.value)

    def negate(self):
        """Negate `self.value`, return reference to self."""
        self.value *= -1
        return self

    @override
    def is_atomic(self, _ctx):
        return True

    @override
    def evaluate(self, _ctx):
        return self


class List(Expression):
    """Represents a list of expressions."""
    def __init__(self, token: Token, expressions: list[Expression]):
        super().__init__(token)
        self.expressions = expressions

    def __str__(self):
        return '[' + ','.join(map(str, self.expressions)) + ']'

    @override
    def is_atomic(self, ctx):
        return all(map(lambda e: e.is_atomic(ctx), self.expressions))

    @override
    def evaluate(self, ctx):
        evaluated = self.expressions[:]

        for i, expression in enumerate(evaluated):
            if expression.is_atomic(ctx) and not isinstance(expression, Variable):
                evaluated[i] = expression
            else:
                evaluated[i] = expression.evaluate(ctx)

                if ctx.eval_step:
                    break

        return List(self.token, evaluated)


class Variable(Expression):
    """Describe a variable (this is *not* the same as an argument)."""
    def __str__(self):
        return self.token.source

    @override
    def is_atomic(self, ctx):
        if str(self) in ctx.bound:
            return False  # 'False' as we can expand

        return True

    @override
    def evaluate(self, ctx):
        if (symbol := str(self)) in ctx.bound:
            value = ctx.bound[symbol]
            return value if ctx.eval_step else value.evaluate(ctx)

        if ctx.force_eval:
            raise NameError(f'{self.token.location()}: free variable \'{symbol}\' encountered')

        return self


class Argument(Expression):
    def __str__(self):
        return self.token.source

    @override
    def substitute(self, old, new):
        return new if self.token.source == old else self

    @override
    def is_atomic(self, ctx):
        return True

    @override
    def evaluate(self, _ctx):
        return self


class UnaryOperation(Expression):
    table = {
        '-': {
            Integer: lambda op, arg: Integer(op.token, -1 * arg.value)
        },
    }

    def __init__(self, token: Token, argument: Expression):
        super().__init__(token)
        self.op = token.source
        self.argument = argument

    def __str__(self):
        return f'{self.op}{bracket_str(self.argument)}'

    @override
    def substitute(self, old, new):
        return UnaryOperation(
            self.token,
            self.argument.substitute(old, new)
        )

    @override
    def is_atomic(self, ctx):
        # if argument can be evaluated, so can we.
        if not self.argument.is_atomic(ctx):
            return False

        # check if operation exists
        for op, variations in UnaryOperation.table.items():
            if op == self.op:
                for c, func in variations.items():
                    if isinstance(self.argument, c):
                        return False

        return True

    @override
    def evaluate(self, ctx):
        # evaluate argument
        if self.argument.is_atomic(ctx) and not isinstance(self.argument, Variable):
            new_arg = self.argument
        else:
            new_arg = self.argument.evaluate(ctx)

            if ctx.eval_step:
                return UnaryOperation(self.token, new_arg)

        # both evaluating any further?
        if not ctx.eval_ops:
            return UnaryOperation(self.token, new_arg)

        # iterate through operation table
        for op, variations in UnaryOperation.table.items():
            if op == self.op:
                for c, func in variations.items():
                    if isinstance(new_arg, c):
                        return func(self, new_arg)

        if ctx.force_eval:
            raise TypeError(f'{self.token.location()}: unsupported argument for operator \'{self.op}\': {new_arg}')

        return UnaryOperation(self.token, new_arg)


class BinaryOperation(Expression):
    table = {
        '+': {
            (Integer, Integer): lambda a, op, b: Integer(op.token, a.value + b.value)
        },
        '-': {
            (Integer, Integer): lambda a, op, b: Integer(op.token, a.value - b.value)
        },
        '*': {
            (Integer, Integer): lambda a, op, b: Integer(op.token, a.value * b.value)
        },
        '/': {
            (Integer, Integer): lambda a, op, b: Integer(op.token, a.value // b.value)
        },
    }

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
    def is_atomic(self, ctx):
        # if argument(s) can be evaluated, so can we.
        if not self.lhs.is_atomic(ctx) or not self.rhs.is_atomic(ctx):
            return False

        # check if operation exists
        for op, variations in BinaryOperation.table.items():
            if op == self.op:
                for (c_lhs, c_rhs), func in variations.items():
                    if isinstance(self.lhs, c_lhs) and isinstance(self.rhs, c_rhs):
                        return False

        return True

    @override
    def evaluate(self, ctx):
        # evaluate left-hand side
        if self.lhs.is_atomic(ctx) and not isinstance(self.lhs, Variable):
            new_lhs = self.lhs
        else:
            new_lhs = self.lhs.evaluate(ctx)

            if ctx.eval_step:
                return BinaryOperation(self.token, new_lhs, self.rhs)

        # evaluate right-hand side
        if self.rhs.is_atomic(ctx) and not isinstance(self.rhs, Variable):
            new_rhs = self.rhs
        else:
            new_rhs = self.rhs.evaluate(ctx)

            if ctx.eval_step:
                return BinaryOperation(self.token, self.lhs, new_rhs)

        # both evaluating any further?
        if not ctx.eval_ops:
            return BinaryOperation(self.token, new_lhs, new_rhs)

        # iterate through operation table
        for op, variations in BinaryOperation.table.items():
            if op == self.op:
                for (c_lhs, c_rhs), func in variations.items():
                    if isinstance(new_lhs, c_lhs) and isinstance(new_rhs, c_rhs):
                        return func(new_lhs, self, new_rhs)

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

    def substitute_argument(self, argument: Expression) -> Expression:
        # provide argument for the function; substitute argument with it.
        return self.body.substitute(str(self.argument), argument)

    @override
    def is_atomic(self, _ctx):
        return True

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
    def is_atomic(self, ctx):
        # if either target or value can be evaluated, so can we
        if not self.target.is_atomic(ctx) or not self.value.is_atomic(ctx):
            return False

        return not isinstance(self.target, Function)

    @override
    def evaluate(self, ctx):
        # evaluate target
        if self.target.is_atomic(ctx):
            new_target = self.target
        else:
            new_target = self.target.evaluate(ctx)

            if ctx.eval_step:
                return Application(self.token, new_target, self.value)

        # evaluate value
        if self.value.is_atomic(ctx):
            new_value = self.value
        else:
            new_value = self.value.evaluate(ctx)

            if ctx.eval_step:
                return Application(self.token, self.target, new_value)

        # if function, we substitute
        if isinstance(new_target, Function):
            result = new_target.substitute_argument(new_value)
            return result if ctx.eval_step else result.evaluate(ctx)

        if ctx.force_eval:
            raise ValueError(
                f'{self.token.location()}: {new_target} is not applicable (attempted to apply {new_value})')

        return Application(self.token, new_target, new_value)

    def __str__(self):
        return f'({bracket_str(self.target)} {bracket_str(self.value)})'
