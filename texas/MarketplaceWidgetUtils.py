#       Copyright 2007 Amazon Technologies, Inc.  Licensed under the Apache License, Version 2.0 (the "License");
#       you may not use this file except in compliance with the License. You may obtain a copy of the License at:
#
#       http://aws.amazon.com/apache2.0
#
#       This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and limitations under the License.
#

import base64
import hmac
import sha

#       Please use Python 2.5.1 or later to run this sample
#       1. Save this file as MarketplaceWidgetUtils.py 
#       2. Run it as:  python MarketplaceWidgetUtils.py 
#       3. You'll see a sample Marketplace widget HTML form as the output.
#       4. You can make a call to the 'getMarketplaceWidgetForm' function as shown in the main function
#       5. You can change the input parameters in the main function below to generate your own Marketplace widget
#       6. This sample, by default, generates a widget which points to the Amazon Payments Sandbox.
#          In order to use your widget in production: 
#          Replace "authorize.payments-sandbox.amazon.com" with "authorize.payments.amazon.com" in the generated HTML
#
#

def main():
        return getMarketplaceWidgetForm("USD %s" % 1,
                "Playa del Fuego Ticket Payment", "1",
                "1", "http://tickets.playadelfuego.org/buy/amazon_process/",
                "http://tickets.playadelfuego.org/buy/amazon_cancel/", "0",
                "http://tickets.playadelfuego.org/buy/amazon_instantpaymentnotification/",
                "tickets@playadelfuego.org")
        #return getMarketplaceWidgetForm("USD 10", "Test Widget", "TxnASD12", "1", "http://yourwebsite.com/return.html", "http://yourwebsite.com/abandon.html", "1", "http://yourwebsite.com/ipn", "pba-ping-recipient@amazon.com", "USD 0.01", "0.04")

def getMarketplaceWidgetForm(amount, description, referenceId = None, immediateReturn = None, returnUrl = None, abandonUrl = None,
                        processImmediate = None, ipnUrl = None, recipientEmail = None,
                        fixedMarketplaceFee = None, variableMarketplaceFee =
                        None, accessKey=None, secretKey=None):
    """
    Generate a signed HTML form for a Pay Now Widget using the inputs provided
    """ 
    self.accessKey = accessKey
    self.secretKey = secretKey
    formHiddenInputs = {'accessKey': accessKey, 'amount': amount, 'description': description}
    if referenceId is not None:
        formHiddenInputs['referenceId'] = referenceId
    if immediateReturn is not None:
        formHiddenInputs['immediateReturn'] = immediateReturn
    if returnUrl is not None:
        formHiddenInputs['returnUrl'] = returnUrl
    if abandonUrl is not None:
        formHiddenInputs['abandonUrl'] = abandonUrl
    if processImmediate is not None:
        formHiddenInputs['processImmediate'] = processImmediate
    if ipnUrl is not None:
        formHiddenInputs['ipnUrl'] = ipnUrl
    if recipientEmail is not None:
        formHiddenInputs['recipientEmail'] = recipientEmail
    if fixedMarketplaceFee is not None:
        formHiddenInputs['fixedMarketplaceFee'] = fixedMarketplaceFee
    if variableMarketplaceFee is not None:
        formHiddenInputs['variableMarketplaceFee'] = variableMarketplaceFee
    stringToSign = getStringToSign(formHiddenInputs)
    signature = calculateRFC210HMAC(stringToSign)
    formHiddenInputs['signature'] = signature
    return getFormHTML(formHiddenInputs)

def getFormHTML(formHiddenInputs):
    form = "<form action=\"https://authorize.payments.amazon.com/pba/paypipeline\" method=\"post\"> \n"
    form = form + "<input type=\"image\" src=\"https://payments.amazon.com/img/btn_m_paynow_126x40_beige_logo.gif\" border=\"0\" class=\"rc_btn_amazon\" > \n"
    formHiddenInputNames = formHiddenInputs.keys()
    parameters = "".join(["<input type=\"hidden\" name=\"" + key + "\" value=\"" + formHiddenInputs[key] + "\" > \n" for key in formHiddenInputNames])
    form = form + parameters + "</form>\n"
    return form

def calculateRFC210HMAC(data):
    """
    Computes a RFC 2104 compliant HMAC Signature and then Base64 encodes it
    """
    return base64.encodestring(hmac.new(self.secretKey, data, sha).digest()).strip()

def getStringToSign(formHiddenInputs):
    formHiddenInputNames = formHiddenInputs.keys()
    formHiddenInputNames.sort(key=str.lower)
    return "".join([key+formHiddenInputs[key] for key in formHiddenInputNames])

if __name__ == '__main__':
    print main()
