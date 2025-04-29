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
          "text": "IMPORTANT: return results with app_response and app_error tools, you don't need to use app_ named tools (but other tools to provide data or actions are ok as needed). \nAfter doing the following, call the app_response tool with response_id=\"kn7vecel2n9\", list_data=your response to the following query as a list of strings. Query: List 10 beautiful flowers with their colors and blooming seasons. For each flower, include its name, a brief description, primary color, and blooming season. If you have trouble calling app_response, can you explicitly return the error message"
        }
      ]
    }
  ],
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