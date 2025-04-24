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
 *    const response = await sendGooseRequest("please give me a list of jokes");
 * 
 * 3. The response will be available via the /wait_for_response/ endpoint asynchronously. 
 * 
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
async function sendGooseRequest(message, responseFormat = 'list', options = {}) {
  // Default options
  const defaults = {
    sessionId: 'web-client-session',
    sessionWorkingDir: '/tmp'
  };

  // generate a random response ID
  const responseId = Math.random().toString(36).substring(2, 15);
  console.log('Generated response ID:', responseId);

  switch (responseFormat) {
    case 'list':
      // Set the response format to list
      message = `After doing the following, call the tool app_response_list with the results of the following query, with response_id=${responseId}. Query:\n ${message}`;
      break;
    case 'table':
      // Set the response format to table
      message = `After doing the following, call the tool app_response_table with the results of the following query, with response_id=${responseId}. Query:\n ${message}`;
      break;
    case 'text':
      // Set the response format to text
      message = `After doing the following, call the tool app_response_str with the results of the following query, with response_id=${responseId}. Query:\n ${message}`;
      break;        
  }
  
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
    //session_id: config.sessionId,
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

      console.log("Received chunk:", chunk);
      
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

/**
 * Parse a single SSE data chunk
 * @param {string} chunk - The SSE data chunk
 * @returns {object|null} Parsed JSON object or null if not valid
 */
function parseSSEChunk(chunk) {
  // Each SSE chunk starts with "data: " and ends with "\n\n"
  if (!chunk.startsWith('data: ')) {
    return null;
  }
  
  // Extract the JSON part
  const jsonStr = chunk.substring(6).trim();
  
  try {
    return JSON.parse(jsonStr);
  } catch (error) {
    console.error('Error parsing SSE chunk:', error);
    return null;
  }
}

