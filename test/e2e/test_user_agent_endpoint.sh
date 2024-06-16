#!/bin/bash
# GIVEN
# The HTTP server has been started.

# WHEN
# Client triggers /user-agent endpoint with User-Agent header.
test_status=0
response_line=$(curl -v --silent http://localhost:4221/user-agent 2>&1 | sed '/^> /d')
status_200=$(echo "$response_line" | grep "< HTTP/1.1 200 OK")
agent_body=$(echo "$response_line" | grep "curl")

# THEN
# 200 OK HTTP status code has to be returned.
if [ -z "$status_200" ]; then
  echo "$response_line"
  error_message="ERROR: 200 status code is expected for /user-agent endpoint"
  test_status=1
fi

# The agent's name has to be returned in the body.
if [ -z "$agent_body" ]; then
  echo "$response_line"
  error_message="ERROR: curl agent is expected for /user-agent endpoint"
  test_status=1
fi

if [ -z "$error_message" ]; then
  echo "$error_message"
fi
exit $test_status
