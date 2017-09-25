from sys import argv, exit
from itertools import dropwhile, filterfalse
from difflib import IS_LINE_JUNK, SequenceMatcher, HtmlDiff
from os.path import basename
import tempfile
import subprocess
import os

def any_in(substrs, line):
    return any(True for _ in
               dropwhile(lambda l: not l in line, substrs))

def is_junk_line(line):
    to_remove = [
        " Attempting to open",
        " EEMA",
        " Eigenvalue=",
        " Improved step=",
        " OPNLGU> ",
        " Other: ",
        " TIME= ",
        " energ=",
        " rnew=",
        "! input data directory",
        "! scratch directory",
        "----------",
        "ALLHP: ",
        "ALLHP> ",
        "CGONNB =",
        "CGOFNB =",
        " Version ",
        "CHARMM>",
        "CLCG Random",
        "CMA: no RDMA devices found",
        "COLLCT_FSTSHK",
        "CPU TIME:",
        "CPU TIME=",
        "CREATED BY USER",
        "Created on",
        "Current HEAP",
        "Current operating system",
        "EANGLC: QANGTYPE =",
        "EANGLE> FORCE: ANGLE NOT FLAT",
        "EANGLE> Using CHARMM angle function",
        "ELAPSED TIME:",
        "Using routine",
        "FCTINI> Surface tension coeff",
        "FREHP: ",
        "FREHP> ",
        "FSSHKINI",
        "Git commit ID",
        "In OpenMM plugin directory",
        "RESIZING",
        "Maximum number of ATOMS:",
        "NBLIST_BUILDER Allocating grid",
        "NUMBER OF ENERGY EVALUATIONS",
        "New timer profile",
        "Number of lone-pairs",
        "OpenMM initiated with",
        "PARRDR> ALL ANGLES HAVE POSITIVE MINIMA",
        "PRINHP> ",
        "Parallel load balance",
        "Parameter #",
        "Parameter: ",
        "Processing passed argument ",
        "QM groups found:",
        "QCHEM: Classical atoms excluded from the QM calculation",
        "RANDOM NUM",
        "RDCMND substituted parameter",
        "Reaction field dielectric",
        "SA modulation: ",
        "SEEDS>",
        "SVN revision",
        "Splitting recip cores into (y by z):",
        "TITLE>",
        "TORQ> No external forces defined",
        "TOTAL NUMBER OF CYCLES",
        "There are no",
        "Total heap storage needed ",
        "Using Column FFT",
        "Using FFTW",
        "Using MKL",
        "Using Pub FFT",
        "VALB CPUC",
        "VCLOSE:",
        "coor. length ",
        "allocated space for coor",
        "emapwrite> ",
        "libOmmXml",
        "libOpenMM",
        "operation not performed",
        "random clcg",
        "reference distance",
        "ISEED ="
    ]
    return any_in(to_remove, line)

def is_skip_line(l): 
    skip_line = False
    if (not "echo" in l.casefold()) and ("test not performed" in l.casefold()):
        skip_line = True

    return skip_line

def is_test_skipped(test_lines):
    return any(map(is_skip_line, test_lines))

def create_filtered_file(lines):
    f_lines = [l for l in lines if not is_junk_line(l)]
    f = tempfile.NamedTemporaryFile()
    for l in f_lines:
        f.write(l.encode())

    f.flush()
    os.fsync(f)
    return f

current_test_file = open(argv[1], errors = 'replace')
current_test_lines = current_test_file.readlines()
current_test_file.close()

test_name = basename(argv[1]).split('.')[0]
print("<testcase name=", test_name, '>', sep = '')

if is_test_skipped(current_test_lines):
    print("  <skipped />")
    print("</testcase>")
    exit(0)
elif any("NO TERMINATION" in l for l in current_test_lines):
    print("  <failure>")
    print("    NO TERMINATION")
    print("  </failure>")
    print("</testcase>")
    exit(0)
elif any("ABNORMAL TERMINATION" in l for l in current_test_lines):
    print("  <failure>")
    print("    ABNORMAL TERMINATION")
    print("  </failure>")
    print("</testcase>")
    exit(0)

curr_file = create_filtered_file(current_test_lines)

previous_test_file = open(argv[2], errors = 'replace')
previous_test_lines = previous_test_file.readlines()
previous_test_file.close()

prev_file = create_filtered_file(previous_test_lines)

diff_result = subprocess.run(['diff', '-qiEbwB', prev_file.name, curr_file.name],
                             stdout = subprocess.PIPE)

if diff_result.returncode != 0:
    diff_proc = subprocess.Popen(['diff',
                                  '-yiEbwB',
                                  '--suppress-common-lines',
                                  prev_file.name,
                                  curr_file.name],
                                 stdout = subprocess.PIPE)
    head_proc = subprocess.Popen(['head'],
                                 stdin = diff_proc.stdout,
                                 stdout = subprocess.PIPE)
    diff_proc.stdout.close()
    diff_lines = head_proc.communicate()[0]

    print("  <failure>")
    print(diff_lines.decode(errors = 'replace'))
    print("  </failure>")

curr_file.close()
prev_file.close()
print("</testcase>")

# p1 = Popen(["dmesg"], stdout=PIPE)
# p2 = Popen(["grep", "hda"], stdin=p1.stdout, stdout=PIPE)
# p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
# output = p2.communicate()[0]
                               
# output=check_output("dmesg | grep hda", shell=True)
