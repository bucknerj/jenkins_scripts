#!/usr/bin/env python3

from sys import argv, exit, stdout
from itertools import dropwhile, filterfalse, islice
from difflib import IS_LINE_JUNK, SequenceMatcher, HtmlDiff
from os.path import basename, isfile, isdir, join
from functools import partial
from lxml import etree

import tempfile
import subprocess
import os
import concurrent.futures
import re
import difflib

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
        result = 'Error'
        if self.failed:
            result = 'Fail'
        if self.skipped:
            result = 'Skip'
        elif self.passed:
            result = 'Pass'
            
        xml = etree.Element('testcase', name = self.name, status = result)

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


        xml.set('time', str(self.time))
        return xml

    def tostring(self):
        return (etree
                .tostring(self.toxml(), pretty_print = True)
                .decode(errors = 'replace'))

def any_in(repats, line):
    return any(True for _ in
               dropwhile(lambda repat: not repat.search(line), repats))

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
    error_lines = [l for l in test_lines if is_error_line(l)]
    if error_lines:
        error_lines = '\n'.join(error_lines)
    elif not [l for l in test_lines if is_normal_stop(l)]:
        error_lines = 'no termination'
        
    return error_lines

def is_fail_line(l):
    fail_line = ''
    if ((not "echo" in l.casefold())
        and (not l.strip().startswith('!'))
        and ('testcase result: fail' in l.casefold())):
        fail_line = l.strip()

    return fail_line

def is_test_failed(test_lines):
    fail_lines = [l for l in test_lines if is_fail_line(l)]
    if fail_lines:
        fail_lines = '\n'.join(fail_lines)
    else:
        fail_lines = ''
    return fail_lines

def is_pass_line(l):
    pass_line = False
    if ((not "echo" in l.casefold())
        and (not l.strip().startswith('!'))
        and ("testcase result: pass" in l.casefold())):
        pass_line = True

    return pass_line

def is_test_passed(test_lines):
    return any(map(is_skip_line, test_lines))

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
    return f_lines

def get_test_time(test_lines):
    test_time = 0.0
    test_time_line = test_lines[-2].split()
    if len(test_time_line) >= 3:
        test_time = test_time_line[2]

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
    return list(islice(diff, 30))

def process_test(to_remove, old_dir, old_fns, new_dir, new_fn):
    with open(join(new_dir, new_fn), errors = 'replace') as new_file:
        new_lines = new_file.readlines()

    test_name = basename(new_fn).split('.')[0]
    test_report = grade_test(test_name, new_lines)
    test_time = get_test_time(new_lines)

    report_lines = ''
    if test_report:
        test_report.time = test_time
    elif not (new_fn in old_fns):
        test_report = TestResult(test_name,
                                 failed = True,
                                 reason = 'NEW TEST',
                                 time = test_time)
    else:
        with open(join(old_dir, new_fn), errors = 'replace') as old_file:
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

def print_results(test_batches, results):
    tot_errors = 0
    tot_failures = 0
    tot_tests = 0
    tot_time = 0.0
    root = etree.Element('testsuites')
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
                              time = str(time))

        tot_errors = tot_errors + nerrors
        tot_failures = tot_failures + nfailures
        tot_tests = tot_tests + ntests
        tot_time = tot_time + time

        for t in batch:
            suite.append(results[t].toxml())

        root.append(suite)
        
    root.set('errors', str(tot_errors))
    root.set('failures', str(tot_failures))
    root.set('tests', str(tot_tests))
    root.set('time', str(tot_time))
    
    print(etree.tostring(root,
                         xml_declaration=True,
                         pretty_print=True).decode(errors = 'replace'))
        
def main():
    if len(argv) < 5:
        print('Usage:', argv[0],
              '<bad patterns file>',
              '<test script home>',
              '<old test dir>', '<new test dir>')
        exit(1)

    to_remove_fn = argv[1]
    test_home = argv[2]
    old_dir = argv[3]
    new_dir = argv[4]

    new_fns = [fn for fn in os.listdir(new_dir)
                    if isfile(join(new_dir, fn))
                    and fn.endswith(".out")]
    old_fns = [fn for fn in os.listdir(old_dir)
                    if isfile(join(old_dir, fn))
                    and fn.endswith(".out")]

    to_remove = []
    with open(to_remove_fn) as to_remove_f:
        to_remove.extend([re.compile(l.strip()) for l in to_remove_f
                          if l.strip() and not l.startswith('#')])

    test_to_file = dict()
    for new_fn in new_fns:
        test_name = basename(new_fn).split('.')[0]
        test_to_file[test_name] = new_fn

    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = zip(test_to_file.keys(),
                      executor.map(partial(process_test,
                                           to_remove,
                                           old_dir, old_fns,
                                           new_dir),
                                   test_to_file.values()))

    test_dirs = [d for d in os.listdir(test_home)
                 if isdir(join(test_home, d))
                 and d.startswith('c')
                 and d.endswith('test')]
    test_batches = dict()
    for dir in test_dirs:
        full_path = join(test_home, dir)
        test_batches[dir] = [basename(fn).split('.')[0]
                             for fn in os.listdir(full_path)
                             if isfile(join(full_path, fn))
                             and fn.endswith('.inp')]

    print_results(test_batches, dict(results))
    exit(0)

if __name__ == '__main__':
    main()
