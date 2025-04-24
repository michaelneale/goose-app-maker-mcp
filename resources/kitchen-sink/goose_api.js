/**
 * Goose API Client
 * 
 * This JavaScript client provides an interface to interact with the Goose API.
 * It handles sending requests and processing streaming responses.
 * 
 * Usage:
 * 1. Include this file in your HTML:
 *    <script src="goose_api.js"></script>
 * 
 * 2. Send a request to the Goose API:
 *    const response = await sendGooseRequest("your message here");
 * 
 * 3. Process the streaming response:
 *    await processStreamingResponse(response, (chunk) => {
 *      console.log("Received chunk:", chunk);
 *    });
 * 
 * Configuration:
 * The client uses environment variables that are replaced at serve time:
 * - $GOOSE_PORT: The port on which the Goose server is running
 * - $GOOSE_SERVER__SECRET_KEY: The secret key for authenticating with the Goose server
 * 
 * These variables are automatically replaced with actual values when the file is served.
 */

// Configuration variables - these will be replaced at serve time
const GOOSE_PORT = '$GOOSE_PORT';
const GOOSE_SERVER__SECRET_KEY = '$GOOSE_SERVER__SECRET_KEY';

// Function to send a request to the Goose API
async function sendGooseRequest(message, options = {}) {
  // Default options
  const defaults = {
    sessionId: 'web-client-session',
    sessionWorkingDir: '/tmp'
  };
  
  // Merge defaults with provided options
  const config = { ...defaults, ...options };
    
  // Create the request body
  const requestBody = {
    messages: [
      {
        role: 'user',
        created: Math.floor(Date.now() / 1000),
        content: [
          {
            type: 'text',
            text: message
          }
        ]
      }
    ],
    session_id: config.sessionId,
    session_working_dir: config.sessionWorkingDir
  };
  
  console.log('Sending request to goose-server on port', GOOSE_PORT);
  console.log('Request body:', JSON.stringify(requestBody, null, 2));
  
  try {
    // Using fetch API for the request
    const response = await fetch(`http://localhost:${GOOSE_PORT}/reply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Secret-Key': GOOSE_SERVER__SECRET_KEY
      },
      body: JSON.stringify(requestBody)
    });
    
    // Check if the response is ok
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    // Return the response for further processing
    return response;
    
  } catch (error) {
    console.error('Error sending request:', error);
    throw error;
  }
}

// Function to process a streaming response
async function processStreamingResponse(response, onChunk) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }
      
      // Decode and process the chunk
      const chunk = decoder.decode(value, { stream: true });
      
      // Call the callback with the chunk
      if (onChunk && typeof onChunk === 'function') {
        onChunk(chunk);
      }
    }
  } catch (error) {
    console.error('Error processing stream:', error);
    throw error;
  }
}