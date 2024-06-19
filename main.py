from lc.lexer import lex
from lc.parser import parse, ParseContext
from lc.structure import EvalContext

if __name__ == "__main__":
    filepath = "./example.lc"

    with open(filepath, 'r') as file:
        statements = lex(file.read())

        parser = ParseContext()
        ctx = EvalContext()

        for statement in statements:
            parser.reset(statement)
            expression = parse(parser)

            print(str(expression))
            print(str(expression.evaluate(ctx)))
