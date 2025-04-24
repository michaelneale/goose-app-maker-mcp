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
 * 2. To get a complete response as a single text:
 *    const text = await getCompleteResponse("your message here");
 *    OR you can use the following options for streaming which gets chunks of data back
 * 
 * 3. Send a request to the Goose API:
 *    const response = await sendGooseRequest("your message here");
 * 
 * 4. Process the streaming response:
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
    //sessionId: 'web-client-session',
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

/**
 * Get a complete response as a single text by assembling all assistant messages
 * @param {string} message - The message to send
 * @param {string} format - preferred format for the response (e.g., "text", "json", "list", "markdown")
 * @param {object} options - Options for the request
 * @returns {Promise<string>} The complete assistant response text
 */
async function getCompleteResponse(message, format="text", options = {}) {

  switch (format) {
    case "markdown":
      message = message + "\n\n# CRITICAL: please format your response as markdown, return only the markdown as requested, no other responses";
      break;
    case "json":  
      message = message + "\n\n# CRITICAL: please format your response as json only, no other responses, a simple mapping of name/value pairs, such as {\"key 1\": \"value 1\", \"key 2\": \"value 2\"}:";
      break;
    case "list": 
      message = message + "\n\n# CRITICAL: please format your response as json list, no other responses, and return no other data, such as ['item 1', 'item 2']:";
  }

  const response = await sendGooseRequest(message, options);
  
  // Initialize variables to store the complete response
  let completeText = '';
  let isFinished = false;
  
  // Process the stream and collect all assistant messages
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  try {
    while (!isFinished) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }
      
      // Decode the chunk and add it to the buffer
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      
      // Process complete SSE messages (they end with double newlines)
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || ''; // Keep the last incomplete chunk in the buffer
      
      for (const message of messages) {
        if (!message.trim()) continue;
        
        const parsedData = parseSSEChunk(message);
        if (!parsedData) continue;
        
        // Check if this is a finish message
        if (parsedData.type === 'Finish') {
          isFinished = true;
          continue;
        }
        
        // Extract text content from assistant messages
        if (parsedData.type === 'Message' && 
            parsedData.message && 
            parsedData.message.role === 'assistant') {
          
          for (const content of parsedData.message.content || []) {
            if (content.type === 'text') {
              completeText += content.text;
            }
          }
        }
      }
    }
    
    // Extract content from code blocks if present
    // Check for code blocks with specific language tags like ```json or ```markdown
    const extractCodeBlock = (text, language) => {
      const regex = new RegExp(`\`\`\`${language}\\s*([\\s\\S]*?)\\s*\`\`\``, 'i');
      const match = text.match(regex);
      return match ? match[1] : null;
    };
    
    // Try to extract JSON content
    const jsonContent = extractCodeBlock(completeText, 'json');
    if (jsonContent) {
      return jsonContent;
    }
    
    // Try to extract Markdown content
    const markdownContent = extractCodeBlock(completeText, 'markdown');
    if (markdownContent) {
      return markdownContent;
    }
    
    return completeText;
    
  } catch (error) {
    console.error('Error processing complete response:', error);
    throw error;
  }
}

/**
 * Get a complete response with all messages and events
 * @param {string} message - The message to send
 * @param {object} options - Options for the request
 * @returns {Promise<Array>} Array of all parsed messages and events
 */
async function getCompleteResponseWithMessages(message, options = {}) {
  const response = await sendGooseRequest(message, options);
  
  // Initialize array to store all messages
  const allMessages = [];
  let isFinished = false;
  
  // Process the stream and collect all messages
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  try {
    while (!isFinished) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }
      
      // Decode the chunk and add it to the buffer
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      
      // Process complete SSE messages (they end with double newlines)
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || ''; // Keep the last incomplete chunk in the buffer
      
      for (const message of messages) {
        if (!message.trim()) continue;
        
        const parsedData = parseSSEChunk(message);
        if (!parsedData) continue;
        
        // Add the parsed message to our collection
        allMessages.push(parsedData);
        
        // Check if this is a finish message
        if (parsedData.type === 'Finish') {
          isFinished = true;
        }
      }
    }
    
    return allMessages;
    
  } catch (error) {
    console.error('Error processing complete response with messages:', error);
    throw error;
  }
}