#!/bin/bash
# GIVEN
# The HTTP server has been started with a served directory.
new_file_content="some text"
new_file_name="test-file"
new_file_path="$TEST_BASE_DIR"/"$new_file_name"

# WHEN
# Client triggers /files/test-file endpoint with body.
response_line=$(curl -v --silent -d "$new_file_content" http://localhost:4221/files/"$new_file_name" 2>&1 | sed '/^> /d')
status_201=$(echo "$response_line" | grep "< HTTP/1.1 201 Created")

# THEN
# 201 CREATED HTTP status code has to be returned.
if [ -z "$status_201" ]; then
  echo Returned response: "$response_line"
  echo "ERROR: 201 status code is expected for /files/{file-name} endpoint"
  rm "$new_file_path"
  exit 1
fi

# New file is created based on url parameter.
if [ ! -f "$new_file_path" ]; then
  echo Returned response: "$response_line"
  echo "ERROR: New file has to be created for /files/{file-name} endpoint"
  rm "$new_file_path"
  exit 1
fi

# Created file has a content from the body.
created_file_content=$(cat "$TEST_BASE_DIR"/test-file)
if [ ! "$created_file_content" == "$new_file_content" ]; then
  echo "ERROR: Created file has to contain the data from the body."
  rm "$new_file_path"
  exit 1
fi

rm "$new_file_path"
exit 0
