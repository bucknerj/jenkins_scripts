#!/bin/env python

import subprocess
import pathlib
import junit_xml as junit


def find_test_suite(test_name):
    pwd_path = pathlib.Path('.')
    test_glob = 'c*test/' + test_name + '.inp'
    test_paths = sorted(pwd_path.glob(test_glob))
    test_suite = 'unknown'
    if len(test_paths) > 0:
        test_suite = test_paths[0].parent.name

    return test_suite


def test_grep(test_name, message, test_dir):
    p = subprocess.run('grep' + ' "' + message + '" ' +
                        test_dir + '/' + test_name + '.out',
                       capture_output=True, text=True, shell=True)

    found = False
    if p.returncode == 0:
        found = True

    return (found, p.stdout.strip())


def get_test_time(test_name, test_dir):
    v, m = test_grep(test_name, 'ELAPSED TIME:', test_dir)
    test_time = 0.0
    m = m.strip()
    if m:
        try:
            test_time_str = m.split()[-2]
            test_time = float(test_time_str)
        except ValueError:
            test_time = 0.0

    return test_time


def main():
    OUTPUT_DIR = "output"
    COMPARE_LOG = "compare.log"
    DIFF_LOG = "diff.log"

    with open(COMPARE_LOG) as compare_file:
        compare_lines = compare_file.readlines()

    compare_lines = [l.split() for l in compare_lines]
    test_names = [l[1] for l in compare_lines]
    test_results = [l[2].startswith("PASS")
                    for l in compare_lines]
    compare = dict(zip(test_names, test_results))

    tests = list()
    for test_name in test_names:
        test_time = get_test_time(test_name, OUTPUT_DIR)
        test = {
            'name': test_name,
            'suite': '',
            'pass': True,
            'skip': False,
            'reason': '',
            'time': test_time,
            'obj': junit.TestCase(name=test_name, elapsed_sec=test_time)
        }
        test['suite'] = find_test_suite(test_name)

        # grep for failed test
        v, m = test_grep(test_name, "RESULT: FAIL", OUTPUT_DIR)
        if v:
            test['pass'] = False
            test['reason'] = m
            test['obj'].add_failure_info(message=m)

        # grep for not finishing
        v, m = test_grep(test_name, "TERMINATION", OUTPUT_DIR)
        if not v:
            m = 'NO TERMINATION'
            test['pass'] = False
            test['reason'] = m
            test['obj'].add_error_info(message=m)

        # grep for charmm error
        v, m = test_grep(test_name, "ABNORMAL TERMINATION",
                         OUTPUT_DIR)
        if v:
            test['pass'] = False
            test['reason'] = m
            test['obj'].add_error_info(message=m)

        # grep for skipped test
        skip_test1, m1 = test_grep(test_name,
                                 "TESTCASE RESULT: SKIP",
                                 OUTPUT_DIR)
        skip_test2, m2 = test_grep(test_name,
                                  "TEST NOT PERFORMED",
                                  OUTPUT_DIR)
        skip_test3, m3 = test_grep(test_name,
                                  "test not performed",
                                  OUTPUT_DIR)
        skip_test = skip_test1 or skip_test2 or skip_test3
        if skip_test and test['pass']:
            m = m1 + m2 + m3
            test['skip'] = True
            test['obj'].add_skipped_info(message=m)

        self_test, m = test_grep(test_name, "TESTCASE RESULT:",
                                 OUTPUT_DIR)
        if not self_test and not compare[test_name] and not test['skip']:
            test['pass'] = False
            test['reason'] = 'BAD DIFF'
            test['obj'].add_failure_info(message='BAD DIFF')

        tests.append(test)

    unique_suites = set([t['suite'] for t in tests])
    suites = list()
    for suite in sorted(unique_suites):
        suite_tests = [t for t in tests if t['suite'] == suite]
        suite_tests = sorted(suite_tests, key=lambda x: x['name'])
        nskips = len([t for t in suite_tests if t['skip']])
        nfails = len([t for t in suite_tests if not t['pass']])
        suites.append({
            'name': suite,
            'tests': suite_tests,
            'fails': nfails,
            'skips': nskips,
            'obj': junit.TestSuite(suite, [t['obj'] for t in suite_tests])
        })

    print(junit.TestSuite.to_xml_string([s['obj'] for s in suites]))


if __name__ == '__main__':
    main()
