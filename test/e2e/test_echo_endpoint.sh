#!/bin/bash
# GIVEN
# The HTTP server has been started.

# WHEN
# Client triggers the root endpoint.
test_status=0
response_line=$(curl -v --silent http://localhost:4221/echo/some-message 2>&1 | sed '/^> /d')
status_200=$(echo "$response_line" | grep "< HTTP/1.1 200 OK")
body_message=$(echo "$response_line" | grep "some-message")

# THEN
# 200 OK HTTP status code has to be returned.
if [ -z "$status_200" ]; then
  echo "$response_line"
  error_message="ERROR: 200 status code is expected for /echo/{message} endpoint"
  test_status=1
fi

# The message from the URL has to be returned in the body.
if [ -z "$body_message" ]; then
  echo "$response_line"
  error_message="ERROR: Body message is expected for /echo/{message} endpoint"
  test_status=1
fi

if [ -z "$error_message" ]; then
  echo "$error_message"
fi
exit $test_status