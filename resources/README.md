# Goose App Maker Resources

This directory contains shared resources that can be used across different Goose apps.

## Available Resources

## example1

A dark mode company analysis dashboard that can be used as a template if needed

## example2

A richer interactive app for performance reporting (but visually basic)


### goose_api.js

A JavaScript client for interacting with the Goose API. This client handles sending requests and processing streaming responses.

#### Usage

1. Include the file in your HTML:
   ```html
   <script src="goose_api.js"></script>
   ```

2. Send a request to the Goose API:
   ```javascript
   const response = await sendGooseRequest("your message here");
   ```

3. Process the streaming response:
   ```javascript
   await processStreamingResponse(response, (chunk) => {
     console.log("Received chunk:", chunk);
     // Update UI with the chunk
   });
   ```

#### Environment Variables

The client uses environment variables that are replaced at serve time:
- `$GOOSE_PORT`: The port on which the Goose server is running
- `$GOOSE_SERVER__SECRET_KEY`: The secret key for authenticating with the Goose server

These variables are automatically replaced with actual values when the file is served by the Goose App Maker server.

#### Full Example

```javascript
// Send a message to the Goose API
async function sendMessage(message) {
  try {
    // Show loading state
    const responseElement = document.getElementById('response');
    responseElement.textContent = 'Loading...';
    
    // Send the request
    const response = await sendGooseRequest(message);
    
    // Clear the loading message
    responseElement.textContent = '';
    
    // Process the streaming response
    await processStreamingResponse(response, (chunk) => {
      // Append each chunk to the response element
      responseElement.textContent += chunk;
    });
    
  } catch (error) {
    console.error('Error:', error);
    const responseElement = document.getElementById('response');
    responseElement.textContent = `Error: ${error.message}`;
  }
}

// Call the function when a button is clicked
document.getElementById('send-button').addEventListener('click', () => {
  const messageInput = document.getElementById('message-input');
  sendMessage(messageInput.value);
});
```