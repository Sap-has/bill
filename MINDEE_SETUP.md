# Bill Tracker with Mindee API Setup

This document explains how to set up the Mindee API integration for the Bill Tracker application to enable receipt scanning functionality.

## Installation

To enable the OCR functionality for receipt scanning using Mindee API, you need to install the Mindee Python package:

```
pip install mindee
```

## Getting a Mindee API Key

1. Sign up for a Mindee account at [https://platform.mindee.com/signup](https://platform.mindee.com/signup)
2. After signing up and logging in, navigate to the API Keys section
3. Create a new API key for the Receipt OCR API
4. Copy your API key to use in the application

## Configuring the Application

1. In the Bill Tracker application, go to the "Bill Entry" tab
2. Right-click on the "Scan Receipt" button
3. Select "Configure Mindee API Key" from the context menu
4. Enter your Mindee API key in the dialog
5. Click "Test API Key" to verify it works
6. Click "Save" to save the API key

## Using Receipt Scanning

Once the API key is configured:

1. In the "Bill Entry" tab, click "Scan Receipt"
2. Select a receipt image from your computer
3. The application will upload the image to Mindee API for processing
4. Once processing is complete, you'll see the extracted information (vendor, date, amount)
5. You can edit this information if needed before applying it to the bill entry form

## Troubleshooting

- If you receive an API key error, verify that your API key is correct and that you have an active Mindee account
- Make sure your internet connection is active, as the API requires an internet connection to process images
- For large or complex receipts, processing may take longer than expected

## Privacy Note

When using the Mindee API, your receipt images are transmitted to Mindee's servers for processing. Please review Mindee's privacy policy at [https://mindee.com/privacy-policy](https://mindee.com/privacy-policy) for more information about how your data is handled. 