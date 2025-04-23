#!/bin/bash

# Create a temporary file for the request body
REQUEST_FILE=$(mktemp)

# Create the JSON request body
cat > "$REQUEST_FILE" << EOF
{
  "messages": [
    {
      "role": "user",
      "created": $(date +%s),
      "content": [
        {
          "type": "text",
          "text": "list files in this dir. Format results as a json array strictly"
        }
      ]
    }
  ],
  "session_id": "curl-test-session",
  "session_working_dir": "/tmp"
}
EOF

echo "Sending request to goose-server on port $GOOSE_PORT..."
echo "Request body:"
cat "$REQUEST_FILE"
echo ""
echo "Response:"

# Send the request and display the streaming response
curl -N -X POST "http://localhost:$GOOSE_PORT/reply" \
  -H "Content-Type: application/json" \
  -H "X-Secret-Key: $GOOSE_SERVER__SECRET_KEY" \
  -d @"$REQUEST_FILE"

# Clean up
rm "$REQUEST_FILE"