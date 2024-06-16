#!/bin/bash
# GIVEN
# The HTTP server has been started.
# Several http requests have been already sent.
(sleep 3 && printf "GET / HTTP/1.1\r\n\r\n") | nc localhost 4221 &
(sleep 3 && printf "GET / HTTP/1.1\r\n\r\n") | nc localhost 4221 &
(sleep 3 && printf "GET / HTTP/1.1\r\n\r\n") | nc localhost 4221 &
(sleep 3 && printf "GET / HTTP/1.1\r\n\r\n") | nc localhost 4221 &

# WHEN
# Client triggers the root endpoint.
test_status=0
response_line=$(sleep 3 && curl -v --silent http://localhost:4221 2>&1 | sed '/^> /d')
status_200=$(echo "$response_line" | grep "< HTTP/1.1 200 OK")

# THEN
# 200 OK HTTP status code has to be returned.
if [ -z "$status_200" ]; then
  echo "$response_line"
  error_message="ERROR: 200 status code is expected for /echo/{message} endpoint"
  test_status=1
fi

if [ -z "$error_message" ]; then
  echo "$error_message"
fi
exit $test_status
