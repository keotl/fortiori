from argparse import ArgumentParser

from dialect.simple_operations import move_function_parameter_type_declaration_to_body, \
    remove_line_splits_inside_blocks, remove_curly_brackets

parser = ArgumentParser(description="FORTRAN transpiler")

parser.add_argument("--output-dir", dest="output_dir", default="out")
parser.add_argument("files", nargs="+", help="files")

args = parser.parse_args()

for file in args.files:
    with open(file, 'r') as f:
        text = f.read()

        text = move_function_parameter_type_declaration_to_body(text)
        text = remove_line_splits_inside_blocks(text)
        text = remove_curly_brackets(text)

        with open(args.output_dir, 'w') as outfile:
            outfile.write(text)
