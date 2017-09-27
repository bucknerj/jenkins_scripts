from sys import argv, exit
from itertools import dropwhile, filterfalse
from difflib import IS_LINE_JUNK, SequenceMatcher, HtmlDiff
from os.path import basename, isfile, isdir, join
from functools import partial
import tempfile
import subprocess
import os
import concurrent.futures
import re

def any_in(repats, line):
    return any(True for _ in
               dropwhile(lambda repat: not repat.search(line), repats))

def is_junk_line(to_remove, line):
    return any_in(to_remove, line)

def is_skip_line(l): 
    skip_line = False
    if (not "echo" in l.casefold()) and ("test not performed" in l.casefold()):
        skip_line = True

    return skip_line

def is_test_skipped(test_lines):
    return any(map(is_skip_line, test_lines))

def create_filtered_file(to_remove, lines):
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

    # write lines to temp file for diffing
    f = tempfile.NamedTemporaryFile()
    for l in f_lines:
        f.write(l.encode())

    f.flush()
    os.fsync(f)
    return f

def grade_test(test_lines):
    report_lines = []
    if is_test_skipped(test_lines):
        report_lines.append("  <skipped />")
    elif any("NO TERMINATION" in l for l in test_lines):
        report_lines.append("  <failure>")
        report_lines.append("    NO TERMINATION")
        report_lines.append("  </failure>")
    elif any("ABNORMAL TERMINATION" in l for l in test_lines):
        report_lines.append("  <failure>")
        report_lines.append("    ABNORMAL TERMINATION")
        report_lines.append("  </failure>")

    return report_lines

def compare_files(to_remove, old_test_lines, new_test_lines):
    old_file = create_filtered_file(to_remove, old_test_lines)
    new_file = create_filtered_file(to_remove, new_test_lines)

    diff_result = subprocess.run(['diff', '-qiEbwB',
                                  old_file.name,
                                  new_file.name],
                                 stdout = subprocess.PIPE)
    report_lines = []
    if diff_result.returncode != 0:
        diff_proc = subprocess.Popen(['diff',
                                      '-yiEbwB',
                                      '--suppress-common-lines',
                                      old_file.name,
                                      new_file.name],
                                     stdout = subprocess.PIPE)
        head_proc = subprocess.Popen(['head'],
                                     stdin = diff_proc.stdout,
                                     stdout = subprocess.PIPE)
        diff_proc.stdout.close()
        diff_lines = head_proc.communicate()[0]
        
        report_lines.append("  <failure>")
        report_lines.extend(diff_lines.decode(errors = 'replace').split(os.linesep))
        report_lines.append("  </failure>")

    old_file.close()
    new_file.close()
    return report_lines

def process_test(to_remove, old_dir, old_fns, new_dir, new_fn):
    new_test_file = open(join(new_dir, new_fn), errors = 'replace')
    new_test_lines = new_test_file.readlines()
    new_test_file.close()
    
    self_report = grade_test(new_test_lines)
    
    test_name = basename(new_fn).split('.')[0]

    new_results = list()
    new_results.append('<testcase name=' + test_name + '>')

    if self_report:
        new_results.extend(self_report)
        new_results.append('</testcase>')
        return new_results

    if not (new_fn in old_fns):
        new_results.extend([
            '  <failure>',
            '    NEW TEST',
            '  </failure>',
            '</testcase>'])
        return new_results
        
    old_test_file = open(join(old_dir, new_fn), errors = 'replace')
    old_test_lines = old_test_file.readlines()
    old_test_file.close()

    report_lines = compare_files(to_remove, old_test_lines, new_test_lines)
    
    if report_lines:
        new_results.extend(report_lines)
            
    new_results.append('</testcase>')
    return new_results

def print_results(test_batches, results):
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<testsuites>')
    for batch_name in sorted(test_batches.keys()):
        batch = [t for t in sorted(test_batches[batch_name])
                 if t in results]
        if batch:
            print('<testsuite name="', batch_name,
                  '" tests="', len(batch), '">',
                  sep='')
            
        for t in batch:
            for l in results[t]:
                print(l)

        if batch:
            print('</testsuite>')

    print('</testsuites>')

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
