//+------------------------------------------------------------------+
//|                                             LicenseChecker.mq5 |
//|                                     Copyright 2026, G-Labs Ltd |
//|                                       https://www.g-labs.software |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, G-Labs Ltd"
#property link      "https://www.g-labs.software"
#property version   "1.00"
#property strict

// Input parameters
input string InpServerURL = "http://localhost:4242"; // Your Server URL (use ngrok for live)
input string InpProductID = "prod_Qwerty123";        // The Product ID from Stripe

// Global Variables
bool IsLicenseValid = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // 1. Check License on Startup
   if(!CheckLicense())
     {
      Alert("LICENSE INVALID! Please purchase a subscription.");
      return(INIT_FAILED);
     }
     
   Print("License Validated Successfully.");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Check License Function                                           |
//+------------------------------------------------------------------+
bool CheckLicense()
  {
   string cookie=NULL, headers;
   char post[], result[];
   string url = InpServerURL + "/api/verify_license";
   
   // Add parameters to URL
   string account = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   string params = "?account_number=" + account + "&product_id=" + InpProductID;
   string full_url = url + params;
   
   // Reset Error
   ResetLastError();
   
   // Send WebRequest (GET)
   int timeout = 5000; // 5 seconds
   int res = WebRequest("GET", full_url, cookie, NULL, timeout, post, 0, result, headers);
   
   if(res == -1)
     {
      Print("Error in WebRequest. Error code  =", GetLastError());
      // MessageBox("Add URL to Allowed URLs in Tools > Options > Expert Advisors", "Error", MB_OK);
      return false;
     }
     
   // Parse Response
   if(res == 200) // HTTP OK
     {
      string response = CharArrayToString(result);
      Print("Server Response: " + response);
      
      // Simple parsing: Look for "valid": true
      // Note: MQL5 doesn't have a native JSON parser, so we do string matching
      if(StringFind(response, "\"valid\": true") >= 0 || StringFind(response, "\"valid\":true") >= 0)
        {
         return true;
        }
     }
     
   return false;
  }
//+------------------------------------------------------------------+
