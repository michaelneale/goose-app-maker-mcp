# Asynchronous Communication with Goose

This document explains how the asynchronous communication between web applications and Goose works in the app-maker system.

## Overview

The system implements a non-blocking, asynchronous request-response pattern that allows web applications to send requests to Goose and receive responses without blocking the main thread. This is achieved through a combination of:

1. A blocking endpoint on the server side
2. Asynchronous JavaScript on the client side
3. A response storage mechanism with thread synchronization

## How It Works

### 1. Client-Side Request Flow

When a client wants to get a response from Goose:

```
┌─────────┐     ┌─────────────────┐     ┌───────────────┐     ┌──────────────┐
│ User    │────▶│ gooseRequestX() │────▶│ Goose API     │────▶│ waitForResp- │
│ Request │     │ (text/list/     │     │ (/reply)      │     │ onse endpoint │
└─────────┘     │  table)         │     └───────────────┘     └──────────────┘
                └─────────────────┘                                   │
                         ▲                                            │
                         │                                            │
                         └────────────────────────────────────────────┘
                                          Response
```

1. The user initiates a request (e.g., clicking "Get List Response")
2. The client calls one of the request functions (`gooseRequestText`, `gooseRequestList`, or `gooseRequestTable`)
3. The function generates a unique `responseId` and sends a request to Goose with instructions to call `app_response` with this ID
4. The function then calls `waitForResponse(responseId)` which polls the `/wait_for_response/{responseId}` endpoint
5. This endpoint blocks until the response is available or a timeout occurs
6. When the response is available, it's returned to the client and displayed

### 2. Server-Side Processing

On the server side:

```
┌─────────────┐     ┌─────────────┐     ┌───────────────┐
│ HTTP Server │────▶│ app_response│────▶│ response_locks│
│ (blocking   │     │ (stores     │     │ (notifies     │
│  endpoint)  │◀────│  response)  │◀────│  waiters)     │
└─────────────┘     └─────────────┘     └───────────────┘
```

1. The `/wait_for_response/{responseId}` endpoint uses condition variables to block until a response is available
2. When Goose processes the request, it calls the `app_response` function with the response data and the `responseId`
3. The `app_response` function stores the response in the `app_responses` dictionary and notifies any waiting threads using the condition variable
4. The blocked HTTP request is then unblocked and returns the response to the client

### 3. Thread Synchronization

The system uses Python's `threading.Condition` for thread synchronization:

1. When a client requests a response that isn't available yet, a condition variable is created for that `responseId`
2. The HTTP handler thread waits on this condition with a timeout (30 seconds)
3. When the response becomes available, the condition is notified
4. If the timeout expires before the response is available, an error is returned

## Key Components

### Client-Side Functions

- `gooseRequestText(query)`: Requests a text response
- `gooseRequestList(query)`: Requests a list response
- `gooseRequestTable(query, columns)`: Requests a table response with specified columns
- `waitForResponse(responseId)`: Waits for a response with the given ID

### Server-Side Functions

- `app_response(response_id, string_data, list_data, table_data)`: Stores a response and notifies waiters
- HTTP handler with `/wait_for_response/{responseId}` endpoint: Blocks until response is available

### Global Storage

- `app_responses`: Dictionary storing responses by ID
- `response_locks`: Dictionary storing condition variables and ready flags by ID

## Benefits

This asynchronous approach provides several benefits:

1. **Non-Blocking UI**: The web application remains responsive while waiting for responses
2. **Efficient Resource Use**: Server threads are only active when processing requests
3. **Timeout Handling**: Requests automatically timeout if responses take too long
4. **Clean Separation**: Clear separation between request sending and response handling

## Limitations

1. **30-Second Timeout**: Responses that take longer than 30 seconds will result in a timeout error
2. **No Progress Updates**: The client has no visibility into request processing progress
3. **No Streaming**: Responses are only delivered when fully complete, not streamed incrementally

## Usage Example

```javascript
// Request a list response
async function getBookRecommendations() {
  try {
    const response = await gooseRequestList("Recommend 5 science fiction books");
    displayResults(response);  // ["Dune", "Neuromancer", "Foundation", ...]
  } catch (error) {
    handleError(error);
  }
}
```