from argparse import ArgumentParser

from fortiori.simple_operations import move_function_parameter_type_declaration_to_body, \
    remove_line_splits_inside_blocks, remove_curly_brackets, strip_comments, \
    move_variable_declaration_to_start_of_block, translate_return_statement, declare_invoked_function_return_types, \
    add_implicit_none, add_name_to_unnamed_program_blocks, translate_case_sensitive_identifier, \
    convert_conditional_blocks, replace_object_reference_type_declaration, inline_pointer_cast_function

parser = ArgumentParser(description="Fortiori FORTRAN transpiler")

parser.add_argument("--output-dir", dest="output_dir", default="out")
parser.add_argument("files", nargs="+", help="files")

args = parser.parse_args()

for file in args.files:
    with open(file, 'r') as f:
        text = f.read()

        text = strip_comments(text)
        text = move_function_parameter_type_declaration_to_body(text)
        text = move_variable_declaration_to_start_of_block(text)
        text = declare_invoked_function_return_types(text)
        text = translate_return_statement(text)
        text = remove_line_splits_inside_blocks(text)
        text = add_implicit_none(text)
        text = translate_case_sensitive_identifier(text)
        text = add_name_to_unnamed_program_blocks(text)
        text = convert_conditional_blocks(text)
        text = inline_pointer_cast_function(text)
        text = replace_object_reference_type_declaration(text)
        text = remove_curly_brackets(text)

        with open(args.output_dir, 'w') as outfile:
            outfile.write(text)
