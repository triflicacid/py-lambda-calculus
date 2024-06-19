from lc.lexer import lex

if __name__ == "__main__":
    filepath = "./example.lc"

    with open(filepath, 'r') as file:
        tokens = lex(file.read())
        print(tokens)
