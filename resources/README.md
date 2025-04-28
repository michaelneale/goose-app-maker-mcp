# Goose App Maker Resources

This directory contains shared resources that can be used across different Goose apps.

## Available Resources

## example1

A dark mode company analysis dashboard that can be used as a template if needed

## example2

A richer interactive app for performance reporting (but visually basic)

## kitchen-sink

A basic but more complete example including how to dynamically fetch data from goose in the app

### kitchen-sink/goose_api.js

A JavaScript client for interacting with the Goose API. This client handles sending requests and receiving responses asynchronously. Copy this file to your app directory to enable communication with Goose.

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

   Note: error reporting is as you develop the app, you can look at app_error tool to fetch recent errors to help debug things for the user on their behalf if things aren't working.

3. The API functions return promises that resolve when the response is available, allowing for asynchronous operation.

4. See the kitchen-sink example for a complete implementation of all three response types.