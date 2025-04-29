# Goose App Maker Resources

This directory contains shared resources that can be used across different Goose apps.

## Available Resources

## example1

A dark mode company analysis dashboard that can be used as a template if needed

## example2

A richer interactive app for performance reporting (but visually basic)

## example3

Simple todo app that persists to localStorage

## example4

A beautiful app that gets a list of flowers from goose and can be refreshed


## kitchen-sink

A basic but more complete example including how to dynamically fetch data from goose in the app. It also demonstrates automatic error handling and reporting.

### kitchen-sink/goose_api.js

A JavaScript client for interacting with the Goose API. This client handles sending requests and receiving responses asynchronously. Copy this file to your app directory to enable communication with Goose.

The goose api allows these apps to talk to a powerful agent to take action, interact with other apis and more. The apis send a message to the agent, and then the agent will provide the data async via another endpoint depending on the structured response requested (see below).

#### Usage

1. Include the file in your HTML:
   ```html
   <script src="goose_api.js"></script>
   ```

2. Request different types of responses from Goose:

   **Text Response**
   ```javascript
   // For paragraph or free text responses
   try {
     const textResponse = await gooseRequestText("Explain how HTTP works in a paragraph");
     console.log(textResponse); // Returns a string
   } catch (error) {
     console.error("Error:", error);
   }
   ```

   **List Response**
   ```javascript
   // For lists of items
   try {
     const listResponse = await gooseRequestList("List 5 popular programming languages");
     console.log(listResponse); // Returns an array of strings
   } catch (error) {
     console.error("Error:", error);
   }
   ```

   **Table Response**
   ```javascript
   // For tabular data (requires column names)
   try {
     const columns = ["Feature", "Description", "Notes"];
     const tableResponse = await gooseRequestTable("Compare the features of 3 popular cloud providers", columns);
     console.log(tableResponse); // Returns an object with columns and rows
     // Format: { columns: ["Feature", "Description", "Notes"], rows: [["Row1Col1", "Row1Col2", "Row1Col3"], ...] }
   } catch (error) {
     console.error("Error:", error);
   }
   ```

   **Error Reporting**
   ```javascript
   // Report errors back to Goose
   try {
     // Some code that might fail
     const data = await fetchData();
     processData(data);
   } catch (error) {
     // Report the error to Goose
     await reportError(`Failed to fetch data: ${error.message}`);
     // You can also display an error message to the user
     showErrorToUser("Failed to load data. The error has been reported.");
   }
   ```

   **Global Error Handling**
   
   The kitchen-sink example includes global error handling that automatically reports all unhandled errors to Goose. To implement this in your app, add the following script to the head of your HTML:
   
   ```javascript
   <script>
     // Global error handler to capture and report all unhandled errors
     window.onerror = function(message, source, lineno, colno, error) {
       // Make sure goose_api.js is loaded before trying to report errors
       if (typeof reportError === 'function') {
         reportError(`Unhandled error: ${message} at ${source}:${lineno}:${colno} | ${error ? error.stack : 'No stack trace available'}`);
       } else {
         console.error('Error occurred before goose_api.js was loaded:', message);
         // Queue the error to be reported once the API is loaded
         window.addEventListener('load', function() {
           if (typeof reportError === 'function') {
             reportError(`Queued error: ${message} at ${source}:${lineno}:${colno} | ${error ? error.stack : 'No stack trace available'}`);
           }
         });
       }
       // Display error in console
       console.error('Global error handler:', message, error);
       // Return true to prevent the default browser error handler
       return true;
     };

     // Capture unhandled promise rejections
     window.addEventListener('unhandledrejection', function(event) {
       const error = event.reason;
       const message = error ? (error.message || 'Unhandled promise rejection') : 'Unhandled promise rejection';
       
       if (typeof reportError === 'function') {
         reportError(`Unhandled promise rejection: ${message} | ${error ? error.stack : 'No stack trace available'}`);
       } else {
         console.error('Promise rejection occurred before goose_api.js was loaded:', message);
         // Queue the error to be reported once the API is loaded
         window.addEventListener('load', function() {
           if (typeof reportError === 'function') {
             reportError(`Queued promise rejection: ${message} | ${error ? error.stack : 'No stack trace available'}`);
           }
         });
       }
       
       console.error('Unhandled promise rejection:', error);
       // Prevent the default handling
       event.preventDefault();
     });
   </script>
   ```

   Note: error reporting is as you develop the app, you can look at app_error tool to fetch recent errors to help debug things for the user on their behalf if things aren't working.

The API functions return promises that resolve when the response is available, allowing for asynchronous operation.