#!/usr/bin/env python3
"""Grade CHARMM test results and generate JUnit XML.

Replaces tool/Compare + compare.awk + new-test-grader.py with a single
script that:
  1. Parses output.rpt (diff report from test.com, already sed-filtered)
  2. Applies numerical tolerance to diff comparisons (ported from compare.awk)
  3. Checks test output files for self-reported status
  4. Generates JUnit XML for Jenkins

The numerical comparison logic is a faithful port of compare.awk by
C.L. Brooks III (Scripps, 2003). For each diff hunk, paired old/new
lines are compared field-by-field: non-numeric fields are treated as 0
(matching awk's string-to-number coercion), and numeric differences are
checked against a relative tolerance with a floor threshold.

Usage:
    python grade-tests.py [--tol 0.0001] [--xfail FILE] > results.xml
"""

import argparse
import os
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

DEFAULT_TOL = 0.0001


# ─── Numerical comparison (ported from compare.awk) ─────────────────

def parse_number(s):
    """Convert string to float, handling Fortran D-notation.

    Returns abs(value) to match compare.awk's abs(tolower(field)+0).
    Returns None for non-numeric strings.
    """
    try:
        return abs(float(s.replace('D-', 'E-').replace('D+', 'E+')
                          .replace('d-', 'e-').replace('d+', 'e+')))
    except (ValueError, AttributeError):
        return None


def is_expected_diff(old_fields, new_fields):
    """Check if a diff line pair is an expected/ignorable difference.

    Ported from compare.awk's exclusion patterns. These cover lines whose
    content is expected to vary between runs (memory addresses, version
    numbers, pair counts from parallel decomposition, etc.).

    Fields are 0-indexed content words (diff prefix stripped).
    compare.awk uses 1-indexed fields where [1]='<', so awk [2] = Python [0].
    """
    def f(fields, i):
        return fields[i] if i < len(fields) else ''

    for fields in (old_fields, new_fields):
        # Memory / address / platform-dependent
        if f(fields, 0) == 'MAXIMUM' and f(fields, 1) == 'SPACE':
            return True
        if f(fields, 1) == 'ADDRESS:':
            return True
        if f(fields, 0) == 'CONTROL' and f(fields, 1) == 'ARRAY':
            return True
        if f(fields, 0) == '>>TESTENDIAN':
            return True
        if f(fields, 0) == 'Number':
            return True
        if f(fields, 0) == 'FORCE=':
            return True
        if f(fields, 0) == 'VCLOSE:':
            return True
        # Correlation coefficient (variable precision)
        if f(fields, 0) == 'CORR.' and f(fields, 1) == 'COEFFICIENT':
            return True
        # Pair counts (parallel decomposition dependent)
        if f(fields, 1) == 'GROUP' and f(fields, 2) == 'PAIRS':
            return True
        if f(fields, 1) == 'PAIRS' and f(fields, 2) == 'USED':
            return True
        if f(fields, 1) == 'ATOM' and f(fields, 2) == 'PAIRS':
            return True
        if f(fields, 3) == 'ATOM' and f(fields, 4) == 'PAIRS':
            return True
        if f(fields, 3) == 'atom' and f(fields, 4) == 'pairs':
            return True
        if f(fields, 3) == 'group' and f(fields, 4) == 'pairs':
            return True
        # Version / build number fields (awk fields [6],[7],[8] = Python [4],[5],[6])
        for i in (4, 5, 6):
            if f(fields, i) in ('99', '5'):
                return True

    # MKIMAT vs MKIMAT2: all fields match except the last
    if (f(old_fields, 2) == 'has' and f(new_fields, 2) == 'has'
            and f(old_fields, 0) == f(new_fields, 0)
            and f(old_fields, 1) == f(new_fields, 1)
            and f(old_fields, 3) == f(new_fields, 3)
            and f(old_fields, 4) == f(new_fields, 4)
            and f(old_fields, 5) == f(new_fields, 5)):
        return True

    return False


def compare_line_pair(old_fields, new_fields, tol):
    """Compare two split lines field-by-field with numerical tolerance.

    Matches compare.awk behavior: non-numeric strings become 0 (awk's
    string+0 coercion). Only numerical differences are checked.

    Returns True if lines are equivalent within tolerance.
    """
    if is_expected_diff(old_fields, new_fields):
        return True

    n = min(len(old_fields), len(new_fields))
    for i in range(n):
        a_raw = parse_number(old_fields[i])
        b_raw = parse_number(new_fields[i])
        a = a_raw if a_raw is not None else 0.0
        b = b_raw if b_raw is not None else 0.0

        diff = abs(a - b)
        denom = max(a, b)
        if denom > tol * tol:
            diff /= denom  # relative error
        if diff > tol and denom > tol:
            return False

    return True


def compare_hunk(old_lines, new_lines, tol):
    """Compare a diff hunk (paired old/new lines).

    Returns (passed, bad_pairs) where bad_pairs is a list of
    (old_line, new_line) tuples that failed the tolerance check.
    """
    n = min(len(old_lines), len(new_lines))
    bad_pairs = []

    for i in range(n):
        of = old_lines[i].split()
        nf = new_lines[i].split()
        if not compare_line_pair(of, nf, tol):
            bad_pairs.append((old_lines[i], new_lines[i]))

    # Different line counts is always a failure (matches compare.awk)
    if len(old_lines) != len(new_lines):
        for line in old_lines[n:]:
            bad_pairs.append((line, ''))
        for line in new_lines[n:]:
            bad_pairs.append(('', line))

    return len(bad_pairs) == 0, bad_pairs


# ─── RPT parsing (replaces tool/Compare) ────────────────────────────

RPT_HEADER = re.compile(r'<\*\*\s+(\S+)\s+:\s+(\S+)\s+\*\*>(.*)')
NOISE_PATTERNS = ('Parallel load', 'New timer')


def parse_rpt(rpt_file):
    """Parse output.rpt into per-test diff data.

    output.rpt is produced by test.com: for each test, it writes a header
    line followed by the raw `diff` output between sed-filtered benchmark
    and test output files.

    Returns dict: {test_name: {'suite': str, 'hunks': [(old, new), ...]}}
    where each hunk is a pair of line lists from a diff block.
    """
    tests = {}
    current_name = None
    current_suite = None
    old_buf = []
    new_buf = []
    hunks = []

    def flush_hunk():
        nonlocal old_buf, new_buf
        if old_buf or new_buf:
            hunks.append((old_buf, new_buf))
            old_buf, new_buf = [], []

    def flush_test():
        nonlocal hunks
        flush_hunk()
        if current_name is not None:
            tests[current_name] = {'suite': current_suite, 'hunks': hunks}
            hunks = []

    lines = []
    if os.path.isfile(rpt_file):
        with open(rpt_file, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

    for line in lines:
        line = line.rstrip('\n')

        m = RPT_HEADER.match(line)
        if m:
            flush_test()
            current_suite = m.group(1)
            current_name = m.group(2)
            continue

        if line.startswith('< '):
            content = line[2:]
            if not any(p in content for p in NOISE_PATTERNS):
                old_buf.append(content)
        elif line.startswith('> '):
            content = line[2:]
            if not any(p in content for p in NOISE_PATTERNS):
                new_buf.append(content)
        elif line.strip() == '---':
            pass  # diff separator between < and > blocks
        else:
            # Non-diff line (diff coordinates, blank, or test.com messages)
            flush_hunk()

    flush_test()
    return tests


# ─── Output file analysis (replaces grep checks) ────────────────────

def read_lines(filepath):
    """Read file lines, returning empty list if missing."""
    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def grep(lines, pattern):
    """Return lines containing pattern, excluding echo/comment lines."""
    matches = []
    for line in lines:
        if pattern in line:
            lower = line.strip().casefold()
            if 'echo' not in lower and not lower.startswith('!'):
                matches.append(line.strip())
    return matches


def get_elapsed_time(lines):
    """Extract ELAPSED TIME from test output (searches from end)."""
    for line in reversed(lines):
        if 'ELAPSED TIME:' in line:
            try:
                return float(line.split()[-2])
            except (ValueError, IndexError):
                pass
    return 0.0


def find_test_suite(test_name):
    """Fallback: find which c##test directory contains this test."""
    for path in sorted(pathlib.Path('.').glob(f'c*test/{test_name}.inp')):
        return path.parent.name
    return 'unknown'


# ─── Test grading ────────────────────────────────────────────────────

def grade_test(test_name, output_dir, rpt_data, tol, xfail):
    """Grade a single test.

    Checks (in order):
      1. xfail list → skipped
      2. Missing output file → error
      3. ABNORMAL TERMINATION → error
      4. No TERMINATION line → error
      5. Self-reported FAIL → failure
      6. Self-reported SKIP → skipped
      7. Self-reported PASS → passed
      8. Diff comparison via output.rpt → failure or passed

    Returns (suite, status_type, message, elapsed).
    status_type is 'error', 'failure', 'skipped', or None (passed).
    """
    lines = read_lines(os.path.join(output_dir, f'{test_name}.out'))
    elapsed = get_elapsed_time(lines)

    # Suite from rpt header, or find by globbing
    suite = rpt_data['suite'] if rpt_data else find_test_suite(test_name)

    if test_name in xfail:
        return suite, 'skipped', 'expected failure (xfail)', elapsed

    if not lines:
        return suite, 'error', 'NO OUTPUT FILE', elapsed

    # Error checks
    abnormal = grep(lines, 'ABNORMAL TERMINATION')
    if abnormal:
        return suite, 'error', '\n'.join(abnormal), elapsed

    if not grep(lines, 'TERMINATION'):
        return suite, 'error', 'NO TERMINATION', elapsed

    # Self-reported status
    fail_result = grep(lines, 'RESULT: FAIL')
    if fail_result:
        return suite, 'failure', '\n'.join(fail_result), elapsed

    skips = (grep(lines, 'TESTCASE RESULT: SKIP') +
             grep(lines, 'TEST NOT PERFORMED') +
             grep(lines, 'test not performed'))
    if skips:
        return suite, 'skipped', '\n'.join(skips), elapsed

    if grep(lines, 'TESTCASE RESULT: PASS'):
        return suite, None, '', elapsed

    # No self-reported status — use diff comparison from output.rpt
    if rpt_data and rpt_data['hunks']:
        all_bad = []
        for old_lines, new_lines in rpt_data['hunks']:
            passed, bad_pairs = compare_hunk(old_lines, new_lines, tol)
            if not passed:
                all_bad.extend(bad_pairs)

        if all_bad:
            details = [f'Numerical comparison failed (tol={tol}):']
            for old, new in all_bad[:20]:
                if old:
                    details.append(f'< {old}')
                if new:
                    details.append(f'> {new}')
            if len(all_bad) > 20:
                details.append(f'... and {len(all_bad) - 20} more differences')
            return suite, 'failure', '\n'.join(details), elapsed

    # No diffs or all within tolerance → passed
    return suite, None, '', elapsed


# ─── JUnit XML output ───────────────────────────────────────────────

def generate_junit(results):
    """Generate JUnit XML from graded results.

    results: list of (test_name, suite, status_type, message, elapsed)
    """
    suites = {}
    for test_name, suite, status_type, message, elapsed in results:
        tc = ET.Element('testcase', name=test_name, time=f'{elapsed:.3f}')
        if status_type and message:
            child = ET.SubElement(tc, status_type)
            child.text = message
        suites.setdefault(suite, []).append(tc)

    testsuites = ET.Element('testsuites')
    for suite_name in sorted(suites):
        cases = sorted(suites[suite_name], key=lambda tc: tc.get('name'))
        n = len(cases)
        n_err = sum(1 for tc in cases if tc.find('error') is not None)
        n_fail = sum(1 for tc in cases if tc.find('failure') is not None)
        n_skip = sum(1 for tc in cases if tc.find('skipped') is not None)
        total_t = sum(float(tc.get('time', 0)) for tc in cases)

        ts = ET.SubElement(testsuites, 'testsuite',
                           name=suite_name, tests=str(n),
                           errors=str(n_err), failures=str(n_fail),
                           skipped=str(n_skip), time=f'{total_t:.3f}')
        for tc in cases:
            ts.append(tc)

    ET.indent(testsuites, space='  ')
    print('<?xml version="1.0" encoding="utf-8"?>')
    print(ET.tostring(testsuites, encoding='unicode'))


# ─── Summary (printed to stderr for Jenkins console) ────────────────

def print_summary(results):
    """Print a human-readable summary to stderr."""
    total = len(results)
    passed = sum(1 for _, _, st, _, _ in results if st is None)
    failed = sum(1 for _, _, st, _, _ in results if st == 'failure')
    errors = sum(1 for _, _, st, _, _ in results if st == 'error')
    skipped = sum(1 for _, _, st, _, _ in results if st == 'skipped')

    print(f'\n  {total} tests: {passed} passed, {failed} failed, '
          f'{errors} errors, {skipped} skipped\n', file=sys.stderr)

    # List failures and errors
    for name, suite, st, msg, _ in results:
        if st == 'failure':
            first_line = msg.split('\n')[0] if msg else ''
            print(f'  FAIL  {suite}/{name}: {first_line}', file=sys.stderr)
        elif st == 'error':
            first_line = msg.split('\n')[0] if msg else ''
            print(f'  ERROR {suite}/{name}: {first_line}', file=sys.stderr)


# ─── Main ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Grade CHARMM test results and generate JUnit XML.',
        epilog='Replaces tool/Compare + compare.awk + new-test-grader.py')
    parser.add_argument('--tol', type=float, default=DEFAULT_TOL,
                        help=f'numerical tolerance (default: {DEFAULT_TOL})')
    parser.add_argument('--xfail', default=None,
                        help='file listing expected-failure test names')
    parser.add_argument('--output-dir', default='output',
                        help='test output directory (default: output)')
    parser.add_argument('--rpt', default='output.rpt',
                        help='diff report from test.com (default: output.rpt)')
    parser.add_argument('--quiet', action='store_true',
                        help='suppress summary on stderr')
    args = parser.parse_args()

    # Load xfail list
    xfail = set()
    if args.xfail and os.path.isfile(args.xfail):
        with open(args.xfail) as f:
            xfail = {line.strip() for line in f
                     if line.strip() and not line.startswith('#')}

    # Parse output.rpt
    rpt = parse_rpt(args.rpt)

    # Find all tests: union of output files and rpt entries
    output_dir = args.output_dir
    test_names = set()
    if os.path.isdir(output_dir):
        for fn in os.listdir(output_dir):
            if fn.endswith('.out'):
                test_names.add(fn[:-4])
    test_names.update(rpt.keys())

    if not test_names:
        print('Error: no test output files or rpt entries found',
              file=sys.stderr)
        sys.exit(1)

    # Grade all tests
    results = []
    for test_name in sorted(test_names):
        rpt_data = rpt.get(test_name)
        suite, status_type, message, elapsed = grade_test(
            test_name, output_dir, rpt_data, args.tol, xfail)
        results.append((test_name, suite, status_type, message, elapsed))

    # Output
    generate_junit(results)
    if not args.quiet:
        print_summary(results)


if __name__ == '__main__':
    main()
