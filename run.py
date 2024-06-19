from sys import argv

from lc.execute import execute


if __name__ == "__main__":
    filepath: str | None = None
    output_raw = False

    for arg in argv[1:]:
        if arg == "--output-raw" and not output_raw:
            output_raw = True
        elif filepath is None:
            filepath = arg
        else:
            raise ValueError(f'Unknown or repeated argument {arg}')

    if filepath is None:
        raise ValueError(f'Expected filepath to be provided')

    with open(filepath, 'r') as file:
        execute(
            file.read(),
            output_raw=output_raw
        )
