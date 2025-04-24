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

A JavaScript client for interacting with the Goose API. This client handles sending requests and processing streaming responses, use this for web apps that need dynamic data by copying it next to other files as needed. This would usually be copied in to the root of each app dir for usage by the web apps

#### Usage

1. Include the file in your HTML:
   ```html
   <script src="goose_api.js"></script>
   ```

2. Send a request to the Goose API:
   ```javascript
     const text = await getCompleteResponse("your message here");
   ```
