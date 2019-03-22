from argparse import ArgumentParser

parser = ArgumentParser(description="FORTRAN transpiler")

parser.add_argument("--output", dest="output", default="out")
parser.add_argument("files", nargs="+", help="files")

args = parser.parse_args()

for file in args.files:
    with open(file, 'r') as f:
        lines = f.readlines()
        
