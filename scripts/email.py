#!/usr/bin/env python3

from lxml import etree
from lxml.builder import E

import os, datetime

workspace = os.environ['WORKSPACE']
build_url = os.environ['BUILD_URL']
job_name = os.environ['JOB_NAME']

output_xml = workspace + '/current/output.xml'
tree = etree.parse(output_xml)

failed = [test.get('name')
          for test in tree.iter(tag = 'testcase')
          if test.get('status') == 'fail']

errors = [test.get('name')
          for test in tree.iter(tag = 'testcase')
          if test.get('status') == 'error']

page = E.html(
    E.head(
        E.title(job_name + ' results')
    ),
    E.body(
        E.p('Results for',
            E.a(job_name, href = build_url),
            'on ',
            str(datetime.datetime.now())
        ),
        E.h3('Failed tests'),
        E.pre('\n'.join(failed)),
        E.h3('Test errors'),
        E.p('abnormal termination or no termination'),
        E.pre('\n'.join(errors))
    )
)

print(etree
      .tostring(page, pretty_print=True)
      .decode(errors = 'replace'))


    


