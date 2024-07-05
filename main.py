import argparse
import os

from src.exam import Exam

# PARSE SCRIPT ARGUMENTS
parser = argparse.ArgumentParser(description='Test multiple HGR metrics on multiple datasets')
parser.add_argument(
    '-s',
    '--sources',
    type=str,
    default='sources',
    help='the path containing the source files'
)
parser.add_argument(
    '-e',
    '--exports',
    type=str,
    default='exports',
    help='the path where to store the exported files'
)
parser.add_argument(
    '--no-lint',
    action='store_true',
    help='does not export the linted source files in .yml'
)
args = parser.parse_args()

# ITERATE THROUGH ALL THE INPUT SOURCES
os.makedirs(args.sources, exist_ok=True)
os.makedirs(args.exports, exist_ok=True)
for file in os.listdir(args.sources):
    Exam(sources=args.sources, exports=args.exports, exam=file).save(lint=not args.no_lint)
