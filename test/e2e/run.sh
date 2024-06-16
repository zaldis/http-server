#!/bin/bash

echo "Set Root directory for the project: $TEST_BASE_DIR"
root_e2e_directory=$(pwd)/test/e2e

# Run HTTP server
cd "$TEST_BASE_DIR" || exit
pipenv run python3 -m app.main --directory "$TEST_BASE_DIR" &
server_pid=$!
sleep 2


# Iterate through the e2e test files and run them
cd "$root_e2e_directory" || exit
for test_file_name in "$root_e2e_directory"/test*
do
  printf "\n\n"
  echo "Run test file: $test_file_name"
  "$test_file_name"
  test_status=$?
  if (( test_status != 0 )); then
    kill $server_pid
    exit $test_status
  else
    echo "$test_file_name - PASSED!"
  fi
done

kill $server_pid
