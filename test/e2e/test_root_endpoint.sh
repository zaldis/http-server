#!/bin/bash

# GIVEN
# The HTTP server has been started

# WHEN
# Client triggers the root endpoint
test_status=0
status_line=$(curl -v --silent http://localhost:4221 2>&1 | grep "< HTTP/1.1 200 OK")

# THEN
# 200 OK HTTP status code has to be returned
if [ -z "$status_line" ]; then
  echo "$status_line"
  error_message="ERROR: 200 status code is expected for / endpoint"
  test_status=1
fi

echo "$error_message"
exit $test_status
