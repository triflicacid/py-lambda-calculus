from lc.execute import execute

if __name__ == "__main__":
    filepath = "./example.lc"

    with open(filepath, 'r') as file:
        execute(file.read())
