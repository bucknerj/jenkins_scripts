#!/usr/bin/env python3

import difflib
import itertools
import os
import os.path
import re
import sys
import tarfile
import xml.etree.ElementTree as EltTree


class TestResult:
    def __init__(self, name, passed=False, error=False, failed=False, skipped=False, reason='', time=0.0):
        self.name = name
        self.passed = passed
        self.error = error
        self.failed = failed
        self.skipped = skipped
        self.reason = reason
        self.time = time

    def toxml(self):
        xml = EltTree.Element('testcase', name=self.name)

        if self.skipped and self.reason:
            skip_child = EltTree.Element('skipped')
            skip_child.text = self.reason
            xml.append(skip_child)
        elif self.failed and self.reason:
            fail_child = EltTree.Element('failure')
            fail_child.text = self.reason
            xml.append(fail_child)
        elif self.error and self.reason:
            error_child = EltTree.Element('error')
            error_child.text = self.reason
            xml.append(error_child)

        xml.set('time', '{0:.3f}'.format(self.time))
        return xml

    def tostring(self):
        return (EltTree
                .tostring(self.toxml())
                .decode(errors='replace'))


def any_in(pats, line):
    return any(True for _ in
               itertools.dropwhile(lambda pat: not pat.search(line), pats))


def is_junk_line(to_remove, line):
    return any_in(to_remove, line)


def is_skip_line(current_line):
    skip_line = False
    if (('echo' not in current_line.casefold())
            and (not current_line.strip().startswith('!'))
            and ('test not performed' in current_line.casefold())):
        skip_line = True

    return skip_line


def is_test_skipped(test_lines):
    skip_lines = [line for line in test_lines if is_skip_line(line)]
    if skip_lines:
        skip_lines = '\n'.join(skip_lines)
    else:
        skip_lines = ''
    return skip_lines


def is_error_line(line):
    error_line = ''
    test_line = line.strip().casefold()
    if (('echo' not in test_line)
            and (not test_line.startswith('!'))
            and ('abnormal termination' in test_line)):
        error_line = line

    return error_line


def is_normal_stop(line):
    end_line = ''
    test_line = line.strip().casefold()
    if test_line.startswith('normal termination'):
        end_line = line

    return end_line


def is_test_error(test_lines):
    error_list = [line for line in test_lines if is_error_line(line)]
    error_lines = '\n'.join(error_list)

    stop_list = []
    if not error_lines:
        stop_list = [line for line in test_lines if is_normal_stop(line)]

    if not error_lines and not stop_list:
        error_lines = 'no termination'

    return error_lines


def is_fail_line(line):
    fail_line = ''
    if (('echo' not in line.casefold())
            and (not line.strip().startswith('!'))
            and ('testcase result: fail' in line.casefold())):
        fail_line = line.strip()

    return fail_line


def is_test_failed(test_lines):
    fail_list = [line for line in test_lines if is_fail_line(line)]
    fail_lines = '\n'.join(fail_list)
    return fail_lines


def is_pass_line(line):
    pass_line = False
    test_line = line.strip().casefold()
    if (('echo' not in test_line)
            and (not test_line.startswith('!'))
            and ('testcase result: pass' in test_line)):
        pass_line = True

    return pass_line


def is_test_passed(test_lines):
    pass_list = [line for line in test_lines if is_pass_line(line)]
    pass_lines = '\n'.join(pass_list)
    return pass_lines


def filter_test(to_remove, lines):
    # delete junk lines
    f_lines = [line for line in lines if not is_junk_line(to_remove, line)]

    # make substitutions
    # s/ \./0\./g
    # s/ -\./-0\./g
    # s/ +\./+0\./g
    # s/  *ISEED =  *1$//

    subs = [(r' \.', '0.'),
            (r' -\.', '-0.'),
            (r' +\.', '+0.'),
            (r'  *ISEED =  *1$', '')]
    subs_comp = [(re.compile(pat), put) for pat, put in subs]
    for pat, put in subs_comp:
        f_lines = [re.sub(pat, put, line) for line in f_lines]

    # delete blank lines
    f_lines = [line for line in f_lines if line.strip()]

    # remove negative zeros: -0.00 -> 0.00, -0 -> 0, -0.05 -> -0.05
    pat = re.compile(r'-(0\.?0*(\s|$))')
    put = r' \1'
    f_lines = [re.sub(pat, put, line) for line in f_lines]

    return f_lines


def get_test_time(test_lines):
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
        test_result = TestResult(test_name, error=True, reason=error_check)
    elif fail_check:
        test_result = TestResult(test_name, failed=True, reason=fail_check)
    elif skip_check:
        test_result = TestResult(test_name, skipped=True, reason=skip_check)
    elif is_test_passed(test_lines):
        test_result = TestResult(test_name, passed=True)

    return test_result


def compare_files(to_remove, old_lines, new_lines):
    old_clean = filter_test(to_remove, old_lines)
    new_clean = filter_test(to_remove, new_lines)

    diff = difflib.context_diff(old_clean, new_clean, 'old', 'new')
    return list(itertools.islice(diff, 30))


def decode_test_file(tar_path, test_name):
    with tarfile.open(tar_path, 'r:*') as tar:
        with tar.extractfile('old/output/' + test_name + '.out') as file:
            lines = file.readlines()

    lines = [line.decode('utf-8', errors='replace') for line in lines]
    return lines


def process_test(to_remove, to_skip, old_dir, old_fns, new_dir, test_name):
    new_lines = decode_test_file(new_dir, test_name)
    test_time = get_test_time(new_lines)
    if any(map(lambda x: x == test_name, to_skip)):
        return TestResult(test_name,
                          skipped=True,
                          reason='test intentionally not graded (see output.xfail)',
                          time=test_time)

    test_report = grade_test(test_name, new_lines)

    report_lines = ''
    fn = 'old/output/' + test_name + '.out'
    if test_report:
        test_report.time = test_time
    elif fn not in old_fns:
        test_report = TestResult(test_name,
                                 failed=True,
                                 reason='NEW TEST',
                                 time=test_time)
    else:
        old_lines = decode_test_file(old_dir, test_name)
        report_lines = compare_files(to_remove, old_lines, new_lines)
        report_lines = ''.join(report_lines)

    if report_lines:
        test_report = TestResult(test_name,
                                 failed=True,
                                 reason=report_lines,
                                 time=test_time)
    elif not test_report:
        test_report = TestResult(test_name,
                                 passed=True,
                                 time=test_time)

    return test_report


def print_results(xml_dir, test_batches, results):
    for batch_name in sorted(test_batches.keys()):
        batch = [t for t in sorted(test_batches[batch_name])
                 if t in results]

        n_tests = len(batch)
        n_errors = len([t for t in batch if results[t].error])
        n_failures = len([t for t in batch if results[t].failed])
        n_skipped = len([t for t in batch if results[t].skipped])
        time = sum([results[t].time for t in batch])

        suite = EltTree.Element('testsuite',
                                name=batch_name,
                                tests=str(n_tests),
                                errors=str(n_errors),
                                failures=str(n_failures),
                                skipped=str(n_skipped),
                                time='{0:.3f}'.format(time))

        for t in batch:
            suite.append(results[t].toxml())

        tree = EltTree.ElementTree(suite)
        output_filename = os.path.join(xml_dir, batch_name + '.xml')
        with open(output_filename, 'w') as output_file:
            tree.write(output_file,
                       encoding='unicode',
                       xml_declaration=True,
                       short_empty_elements=False)


def main():
    if len(sys.argv) < 7:
        print('Usage:', sys.argv[0],
              '<bad patterns file>',
              '<tests to ignore file>',
              '<test script home>',
              '<old test dir>', '<new test dir>',
              '<output dir>')
        sys.exit(1)

    to_remove_fn = sys.argv[1]
    to_skip_fn = sys.argv[2]
    test_home = sys.argv[3]
    old_dir = sys.argv[4]
    new_dir = sys.argv[5]
    xml_dir = sys.argv[6]

    with tarfile.open(new_dir, 'r:*') as new_tar:
        new_fns = [fn for fn in new_tar.getnames() if fn.endswith('.out')]

    with tarfile.open(old_dir, 'r:*') as old_tar:
        old_fns = [fn for fn in old_tar.getnames() if fn.endswith('.out')]

    with open(to_remove_fn) as to_remove_f:
        to_remove = [re.compile(line.strip()) for line in to_remove_f
                     if line.strip() and not line.startswith('#')]

    with open(to_skip_fn) as to_skip_f:
        to_skip = [line.strip() for line in to_skip_f
                   if line.strip() and not line.startswith('#')]

    test_names = [os.path.basename(fn[:-4]) for fn in new_fns]
    test_results = [process_test(to_remove, to_skip, old_dir, old_fns, new_dir, name) for name in test_names]
    test_dirs = [d for d in os.listdir(test_home)
                 if os.path.isdir(os.path.join(test_home, d))
                 and re.match(r'c\d{2}test', d)]

    test_batches = dict()
    for current_dir in test_dirs:
        full_path = os.path.join(test_home, current_dir)
        test_batches[current_dir] = [os.path.basename(fn)[:-4]
                                     for fn in os.listdir(full_path)
                                     if os.path.isfile(os.path.join(full_path,
                                                                    fn))
                                     and fn.endswith('.inp')]

    results = zip(test_names, test_results)
    print_results(xml_dir, test_batches, dict(results))
    sys.exit(0)


if __name__ == '__main__':
    main()
