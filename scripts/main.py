import argparse
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exam import Exam

# PARSE SCRIPT ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument(
    '-s',
    '--sources',
    type=str,
    default='../sources',
    help='the path containing the source files'
)
parser.add_argument(
    '-e',
    '--exports',
    type=str,
    default='../exports',
    help='the path where to store the exported files'
)
parser.add_argument(
    '--lint',
    action='store_true',
    help='exports the linted source files in .yml'
)
args = parser.parse_args()

# ITERATE THROUGH ALL THE INPUT SOURCES
os.makedirs(args.sources, exist_ok=True)
os.makedirs(args.exports, exist_ok=True)

for file in os.listdir(args.sources):
    if re.search(r'\.ya?ml$', file):
        Exam(sources=args.sources, exports=args.exports, exam=file).save(lint=args.lint)
