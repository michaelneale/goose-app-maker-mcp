# Goose App Maker Resources

This directory contains shared resources that can be used across different Goose apps.

## Available Resources

## example1

A dark mode company analysis dashboard that can be used as a template if needed

## example2

A richer interactive app for performance reporting (but visually basic)

## kitchen-sink

A basic but more complete example including how to dynamically fetch data from goose in the app

### goose_api.js

A JavaScript client for interacting with the Goose API. This client handles sending requests and processing streaming responses, use this for web apps that need dynamic data by copying it next to other files as needed.

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

The client uses environment variables that are replaced at serve time, you don't need to worry about these.
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