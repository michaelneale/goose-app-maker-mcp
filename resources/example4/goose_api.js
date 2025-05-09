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
 * 2. Send a request to the Goose API using one of these functions:
 *    - gooseRequestText("What is the capital of France?")
 *    - gooseRequestList("Give me a list of 5 book recommendations")
 *    - gooseRequestTable("Show me sales data by region", ["Region", "Revenue", "Growth"])
 *    - reportError("An error occurred: Unable to load data")
 * 
 * 3. Each function returns a Promise that resolves with the response data.
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

/**
 * Generate a random session ID for interaction with Goose
 */
function generateSessionId() {
  return Math.random().toString(36).substring(2, 15);
}

const gooseAppSession = generateSessionId();


/**
 * Send a request to Goose and wait for the response
 * @param {string} message - The message to send to Goose
 * @returns {Promise} A promise that resolves when the response is received
 */
async function sendGooseRequestAndWait(message) {
  // Reset any previous response state
  try {
    await fetch('/wait_for_response/reset');
    console.log('Response state reset');
  } catch (error) {
    console.warn('Failed to reset response state:', error);
    // Continue anyway
  }
      
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
    session_working_dir: '/tmp', 
    session_id: gooseAppSession,
  };
  
  console.log('Sending request to goose-server on port', GOOSE_PORT);
  console.log('Request body:', JSON.stringify(requestBody, null, 2));
  
  try {
    // Send the request to Goose
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
    
    console.log('Request sent successfully, waiting for response');
    
    // Wait for the response to be available
    const waitResponse = await waitForResponse();
    return waitResponse;
    
  } catch (error) {
    console.error('Error sending request:', error);
    throw error;
  }
}

/**
 * Wait for a response
 * @returns {Promise} A promise that resolves with the response data
 */
async function waitForResponse() {
  console.log('Waiting for response');
  
  try {
    // Poll the wait_for_response endpoint
    const response = await fetch(`/wait_for_response`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Response received:', result.data);
      return result.data;
    } else {
      throw new Error(result.error || 'Unknown error waiting for response');
    }
  } catch (error) {
    console.error('Error waiting for response:', error);
    throw error;
  }
}

/**
 * Request a text response from Goose
 * @param {string} query - The query to send to Goose
 * @returns {Promise<string>} A promise that resolves with the text response
 */
async function gooseRequestText(query) {
  const message = `Return the results from the query, by calling the app_response tool with string_data parameter.\n Query:\n ${query}`;
  
  return sendGooseRequestAndWait(message);
}

/**
 * Request a list response from Goose
 * @param {string} query - The query to send to Goose
 * @returns {Promise<Array<string>>} A promise that resolves with the list response
 */
async function gooseRequestList(query) {
  const message = `Return the results from the query, by calling the app_response tool with the list_data parameter as a list of strings. Query: ${query}`;
  
  return sendGooseRequestAndWait(message);
}

/**
 * Request a table response from Goose
 * @param {string} query - The query to send to Goose
 * @param {Array<string>} columns - The column names for the table (required)
 * @returns {Promise<Object>} A promise that resolves with the table response
 */
async function gooseRequestTable(query, columns) {
  if (!columns || !Array.isArray(columns) || columns.length === 0) {
    throw new Error("Column names are required for table requests");
  }
  
  let message = `Return the results from the query, by calling the app_response tool with table_data parameter`;
  
  message += ` Use these columns: ${JSON.stringify(columns)}.`;
  message += ` The table_data should be in this format: {"columns": ${JSON.stringify(columns)}, "rows": [["row1col1", "row1col2", ...], ...]}`;
  message += ` Query: ${query}`;
  
  return sendGooseRequestAndWait(message);
}

/**
 * Report an error to Goose
 * @param {string} errorMessage - The error message to report
 * @returns {Promise<string>} A promise that resolves with a confirmation message
 */
async function reportError(errorMessage) {
  if (!errorMessage) {
    throw new Error("Error message is required");
  }
  
  
  // Create the message instructing Goose to call app_error
  const message = `Call the app_error tool with this error message: ${errorMessage}`;
  
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
    session_working_dir: '/tmp', 
    session_id: gooseAppSession,
  };
  
  try {
    // Send the request to Goose
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
    
    console.log('Error reported to Goose:', errorMessage);
    return `Error reported: ${errorMessage}`;
    
  } catch (error) {
    console.error('Error reporting to Goose:', error);
    throw error;
  }
}

