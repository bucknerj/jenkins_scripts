#!/usr/bin/env python3

import concurrent.futures
import difflib
import functools
import itertools
import os
import os.path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as etree

class TestResult:
    def __init__(self, name, passed = False, error = False, failed = False, skipped = False, reason = '', time = 0.0):
        self.name = name
        self.passed = passed
        self.error = error
        self.failed = failed
        self.skipped = skipped
        self.reason = reason
        self.time = time

    def toxml(self):
        result = 'error'
        if self.failed:
            result = 'fail'
        if self.skipped:
            result = 'skip'
        elif self.passed:
            result = 'pass'

        xml = etree.Element('testcase', name = self.name)

        if self.skipped and self.reason:
            skip_child = etree.Element('skipped')
            skip_child.text = self.reason
            xml.append(skip_child)
        elif self.failed and self.reason:
            fail_child = etree.Element('failure')
            fail_child.text = self.reason
            xml.append(fail_child)
        elif self.error and self.reason:
            error_child = etree.Element('error')
            error_child.text = self.reason
            xml.append(error_child)

        xml.set('time', '{0.3g}'.format(self.time))
        return xml

    def tostring(self):
        return (etree
                .tostring(self.toxml(), pretty_print = True)
                .decode(errors = 'replace'))

def any_in(repats, line):
    return any(True for _ in
               itertools.dropwhile(lambda repat: not repat.search(line), repats))

def is_junk_line(to_remove, line):
    return any_in(to_remove, line)

def is_skip_line(l):
    skip_line = False
    if ((not 'echo' in l.casefold())
        and (not l.strip().startswith('!'))
        and ('test not performed' in l.casefold())):
        skip_line = True

    return skip_line

def is_test_skipped(test_lines):
    skip_lines = [l for l in test_lines if is_skip_line(l)]
    if skip_lines:
        skip_lines = '\n'.join(skip_lines)
    else:
        skip_lines = ''
    return skip_lines

def is_error_line(l):
    error_line = ''
    test_line = l.strip().casefold()
    if ((not 'echo' in test_line)
        and (not test_line.startswith('!'))
        and ('abnormal termination' in test_line)):
        error_line = l

    return error_line

def is_normal_stop(l):
    end_line = ''
    test_line = l.strip().casefold()
    if test_line.startswith('normal termination'):
        end_line = l

    return end_line

def is_test_error(test_lines):
    error_list = [l for l in test_lines if is_error_line(l)]
    error_lines = '\n'.join(error_list)

    stop_list = []
    if not error_lines:
        stop_list = [l for l in test_lines if is_normal_stop(l)]

    if not error_lines and not stop_list:
        error_lines = 'no termination'

    return error_lines

def is_fail_line(l):
    fail_line = ''
    if ((not 'echo' in l.casefold())
        and (not l.strip().startswith('!'))
        and ('testcase result: fail' in l.casefold())):
        fail_line = l.strip()

    return fail_line

def is_test_failed(test_lines):
    fail_list = [l for l in test_lines if is_fail_line(l)]
    fail_lines = '\n'.join(fail_list)
    return fail_lines

def is_pass_line(l):
    pass_line = False
    test_line = l.strip().casefold()
    if ((not 'echo' in test_line)
        and (not test_line.startswith('!'))
        and ('testcase result: pass' in test_line)):
        pass_line = True

    return pass_line

def is_test_passed(test_lines):
    pass_list = [l for l in test_lines if is_pass_line(l)]
    pass_lines = '\n'.join(pass_list)
    return pass_lines

def filter_test(to_remove, lines):
    # delete junk lines
    f_lines = [l for l in lines if not is_junk_line(to_remove, l)]

    # make substitutions
    # s/ \./0\./g
    # s/ -\./-0\./g
    # s/ +\./+0\./g
    # s/  *ISEED =  *1$//

    subs = [(' \.', '0.'),
            (' -\.', '-0.'),
            (' +\.', '+0.'),
            ('  *ISEED =  *1$', '')]
    subs_comp = [(re.compile(pat), repl) for pat, repl in subs]
    for pat, repl in subs_comp:
        f_lines = [re.sub(pat, repl, l) for l in f_lines]

    # delete blank lines
    f_lines = [l for l in f_lines if l.strip()]

    # remove negative zeros: -0.00 -> 0.00, -0 -> 0, -0.05 -> -0.05
    pat = re.compile('-(0\.?0*(\s|$))')
    repl = r' \1'
    f_lines = [re.sub(pat, repl, l) for l in f_lines]

    return f_lines

def get_test_time(test_lines):
    test_time = 0.0

    try:
        test_time_line = test_lines[-2].split()
        test_time = test_time_line[2]
    except IndexError:
        test_time = 0.0

    try:
        test_time = float(test_time)
    except ValueError:
        test_time = 0.0

    return test_time

def grade_test(test_name, test_lines):
    test_result = None
    error_check = is_test_error(test_lines)

    fail_check = None
    if not error_check:
        fail_check = is_test_failed(test_lines)

    skip_check = None
    if not (fail_check or error_check):
        skip_check = is_test_skipped(test_lines)

    if error_check:
        test_result = TestResult(test_name, error = True, reason = error_check)
    elif fail_check:
        test_result = TestResult(test_name, failed = True, reason = fail_check)
    elif skip_check:
        test_result = TestResult(test_name, skipped = True, reason = skip_check)
    elif is_test_passed(test_lines):
        test_result = TestResult(test_name, passed = True)

    return test_result

def compare_files(to_remove, old_lines, new_lines):
    old_clean = filter_test(to_remove, old_lines)
    new_clean = filter_test(to_remove, new_lines)

    diff = difflib.context_diff(old_clean, new_clean, 'old', 'new')
    return list(itertools.islice(diff, 30))

def process_test(to_remove, to_skip, old_dir, old_fns, new_dir, new_fn):

    with open(os.path.join(new_dir, new_fn), errors = 'replace') as new_file:
        new_lines = new_file.readlines()

    test_name = os.path.basename(new_fn).split('.')[0]
    test_time = get_test_time(new_lines)

    if any(map(lambda x: x == test_name, to_skip)):
        return TestResult(test_name,
                          skipped = True,
                          reason = 'test intentionally not graded (see output.xfail)',
                          time = test_time)

    test_report = grade_test(test_name, new_lines)


    report_lines = ''
    if test_report:
        test_report.time = test_time
    elif not (new_fn in old_fns):
        test_report = TestResult(test_name,
                                 failed = True,
                                 reason = 'NEW TEST',
                                 time = test_time)
    else:
        with open(os.path.join(old_dir, new_fn), errors = 'replace') as old_file:
            old_lines = old_file.readlines()

        report_lines = compare_files(to_remove, old_lines, new_lines)
        report_lines = ''.join(report_lines)

    if report_lines:
        test_report = TestResult(test_name,
                                 failed = True,
                                 reason = report_lines,
                                 time = test_time)
    elif not test_report:
        test_report = TestResult(test_name,
                                 passed = True,
                                 time = test_time)

    return test_report

def print_results(xml_fname, test_batches, results):
    first = True
    for batch_name in sorted(test_batches.keys()):
        batch = [t for t in sorted(test_batches[batch_name])
                 if t in results]

        ntests = len(batch)
        nerrors = len([t for t in batch if results[t].error])
        nfailures = len([t for t in batch if results[t].failed])
        nskipped = len([t for t in batch if results[t].skipped])
        time = sum([results[t].time for t in batch])

        suite = etree.Element('testsuite',
                              name = batch_name,
                              tests = str(ntests),
                              errors = str(nerrors),
                              failures = str(nfailures),
                              skipped = str(nskipped),
                              time = '{0:.3g}'.format(time))

        for t in batch:
            suite.append(results[t].toxml())

        tree = etree.ElementTree(suite)
        tree.write(xml_fname,
                   xml_declaration = first,
                   short_empty_elements = False)
        first = False

def main():
    if len(sys.argv) < 6:
        print('Usage:', sys.argv[0],
              '<bad patterns file>',
              '<tests to ignore file>',
              '<test script home>',
              '<old test dir>', '<new test dir>')
        sys.exit(1)

    to_remove_fn = sys.argv[1]
    to_skip_fn = sys.argv[2]
    test_home = sys.argv[3]
    old_dir = sys.argv[4]
    new_dir = sys.argv[5]
    xml_fname = sys.argv[6]

    new_fns = [fn for fn in os.listdir(new_dir)
                    if os.path.isfile(os.path.join(new_dir, fn))
                    and fn.endswith(".out")]
    old_fns = [fn for fn in os.listdir(old_dir)
                    if os.path.isfile(os.path.join(old_dir, fn))
                    and fn.endswith(".out")]

    to_remove = []
    with open(to_remove_fn) as to_remove_f:
        to_remove.extend([re.compile(l.strip()) for l in to_remove_f
                          if l.strip() and not l.startswith('#')])

    to_skip = []
    with open(to_skip_fn) as to_skip_f:
        to_skip.extend([l.strip() for l in to_skip_f
                          if l.strip() and not l.startswith('#')])

    test_to_file = dict()
    for new_fn in new_fns:
        test_name = os.path.basename(new_fn).split('.')[0]
        test_to_file[test_name] = new_fn

    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = zip(test_to_file.keys(),
                      executor.map(functools.partial(process_test,
                                           to_remove, to_skip,
                                           old_dir, old_fns,
                                           new_dir),
                                   test_to_file.values()))

    test_dirs = [d for d in os.listdir(test_home)
                 if os.path.isdir(os.path.join(test_home, d))
                 and d.startswith('c')
                 and d.endswith('test')]
    test_batches = dict()
    for dir in test_dirs:
        full_path = os.path.join(test_home, dir)
        test_batches[dir] = [os.path.basename(fn).split('.')[0]
                             for fn in os.listdir(full_path)
                             if os.path.isfile(os.path.join(full_path, fn))
                             and fn.endswith('.inp')]

    print_results(xml_fname, test_batches, dict(results))
    sys.exit(0)

if __name__ == '__main__':
    main()
