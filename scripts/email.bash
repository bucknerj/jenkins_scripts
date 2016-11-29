#!/bin/bash

output_xml=$WORKSPACE/current/output.xml
output_xfail=$WORKSPACE/current/output.xfail
charmm_src=$WORKSPACE/inst
charmm_test_dir=$charmm_src/test

fails=$(grep -E -B 2 'FAILURE|CRASH|MISSING' "$output_xml" | \
    grep testcase | \
    sed -e 's/\s*<testcase name="\(.*\)">/\1/')

echo '<!DOCTYPE html>'
echo '<html>'
echo '<head>'
echo "<title>$JOB_NAME results</title>"
echo '</head>'
echo '<body>'

echo '<p>Results for'
echo "<a href=\"$BUILD_URL\">$JOB_NAME</a>"
echo "on $(date)</p>"

echo '<h3>New test failures</h3>'
if [[ $fails = *[![:space:]]* ]]; then
    echo '<pre>'
    for fail in $fails; do
        cno=$(basename $(dirname $(ls $charmm_test_dir/c*test/$fail.inp)))
        echo "$cno/$fail"
    done
    echo '</pre>'
else
    echo '<p>No new test failures</p>'
fi

echo '<h3>Skipped previous failures</h3>'
skipped=$(cat "$output_xfail")
if [[ $skipped = *[![:space:]]* ]]; then
    echo '<pre>'
    echo -e "$skipped"
    echo '</pre>'
else
    echo '<p>No skipped previous failures</p>'
fi

echo '</body>'
echo '</html>'
