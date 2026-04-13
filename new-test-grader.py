#!/usr/bin/env python3
"""Generate JUnit XML test reports from CHARMM test results.

Reads compare.log (from tool/Compare) and test output files to grade
each test as pass/fail/skip/error, then writes JUnit XML to stdout.

Usage:
    python new-test-grader.py [--xfail FILE] [--output-dir DIR] [--compare-log FILE]
"""

import argparse
import os
import pathlib
import re
import sys
import xml.etree.ElementTree as ET


COMPARE_PAT = re.compile(r'TEST\s+(\S+)\s+(PASS|FAIL)')


def find_test_suite(test_name):
    """Find which c##test directory contains this test."""
    for path in sorted(pathlib.Path('.').glob(f'c*test/{test_name}.inp')):
        return path.parent.name
    return 'unknown'


def read_lines(filepath):
    """Read file lines, returning empty list if file doesn't exist."""
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


def grade_test(test_name, output_dir, compare_passed, xfail):
    """Grade a single test, returning (status_type, message, elapsed).

    status_type is one of: 'error', 'failure', 'skipped', or None (passed).
    """
    lines = read_lines(os.path.join(output_dir, f'{test_name}.out'))
    elapsed = get_elapsed_time(lines)

    if test_name in xfail:
        return 'skipped', 'expected failure (xfail)', elapsed

    if not lines:
        return 'error', 'NO OUTPUT FILE', elapsed

    # Check for abnormal termination (error)
    abnormal = grep(lines, 'ABNORMAL TERMINATION')
    if abnormal:
        return 'error', '\n'.join(abnormal), elapsed

    # Check for no termination (error)
    if not grep(lines, 'TERMINATION'):
        return 'error', 'NO TERMINATION', elapsed

    # Check for explicit FAIL result
    fail_result = grep(lines, 'RESULT: FAIL')
    if fail_result:
        return 'failure', '\n'.join(fail_result), elapsed

    # Check for skip markers
    skips = (grep(lines, 'TESTCASE RESULT: SKIP') +
             grep(lines, 'TEST NOT PERFORMED') +
             grep(lines, 'test not performed'))
    if skips:
        return 'skipped', '\n'.join(skips), elapsed

    # Check diff comparison — only if test has no self-reported result
    self_test = grep(lines, 'TESTCASE RESULT:')
    if not self_test and not compare_passed:
        return 'failure', 'BAD DIFF', elapsed

    return None, '', elapsed  # passed


def main():
    parser = argparse.ArgumentParser(description='Grade CHARMM test results')
    parser.add_argument('--xfail', default=None,
                        help='File listing expected-failure test names')
    parser.add_argument('--output-dir', default='output',
                        help='Test output directory (default: output)')
    parser.add_argument('--compare-log', default='compare.log',
                        help='Compare log from tool/Compare (default: compare.log)')
    args = parser.parse_args()

    # Load xfail list
    xfail = set()
    if args.xfail and os.path.isfile(args.xfail):
        with open(args.xfail) as f:
            xfail = {line.strip() for line in f
                     if line.strip() and not line.startswith('#')}

    # Parse compare.log
    compare = {}
    for line in read_lines(args.compare_log):
        m = COMPARE_PAT.search(line)
        if m:
            compare[m.group(1)] = (m.group(2) == 'PASS')

    if not compare:
        print('Error: no test results found in', args.compare_log,
              file=sys.stderr)
        sys.exit(1)

    # Grade each test
    suites = {}
    for test_name in compare:
        status_type, message, elapsed = grade_test(
            test_name, args.output_dir, compare.get(test_name, True), xfail)

        tc = ET.Element('testcase', name=test_name, time=f'{elapsed:.3f}')
        if status_type and message:
            ET.SubElement(tc, status_type).text = message

        suite_name = find_test_suite(test_name)
        suites.setdefault(suite_name, []).append(tc)

    # Build XML output
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


if __name__ == '__main__':
    main()
