if in request transactionId is missing  then the below xml should be populated :-

<soapenv:Envelope xmlns:nsVer="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <nsVer:validateArrangementForPaymentResponse>
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e3176838795e35859a4d20250529161230076h</transactionId>
            </responseId>
            <operatingBrand>ALL</operatingBrand>
            <serviceName>ArrValidationForPayment</serviceName>
            <operationName>validateArrangementForPayment</operationName>
            <cmdStatus>Failed</cmdStatus>
            <cmdNotifications>
               <returnCode>ERR006</returnCode>
               <category>Error</category>
               <description>Unable to Complete Request</description>
               <timestamp>2025-05-29T16:12:30.156996+01:00</timestamp>
               <systemNotifications>
                  <returnCode>0060</returnCode>
                  <category>Error</category>
                  <description>Invalid Transaction Id</description>
                  <processingId>
                     <systemId>PMP</systemId>
                  </processingId>
               </systemNotifications>
            </cmdNotifications>
         </exception>
      </nsVer:validateArrangementForPaymentResponse>
   </soapenv:Body>
</soapenv:Envelope>

---------
for any other schema validation error :-


<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Header/>
   <soap:Body>
      <tns:validateArrangementForPaymentResponse xmlns:tns="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/">
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e31768387a463585a54d20250529161622007h</transactionId>
            </responseId>
            <refRequestIds>
               <systemId>RequestID</systemId>
               <transactionId>123456789</transactionId>
            </refRequestIds>
            <operatingBrand>ALL</operatingBrand>
            <serviceName>ArrValidationForPayment</serviceName>
            <operationName>validateArrangementForPayment</operationName>
            <cmdStatus>Failed</cmdStatus>
            <cmdNotifications>
               <returnCode>ERR001</returnCode>
               <category>Error</category>
               <description>Message Not Formatted Correctly. Validation of the message failed in the request, response or exception e.g. XSD or WSDL validations. The input message has failed schema validation for service operation validateArrangementForPayment.</description>
               <timestamp>2025-05-29T16:16:22+01:00</timestamp>
            </cmdNotifications>
         </exception>
      </tns:validateArrangementForPaymentResponse>
   </soap:Body>
</soap:Envelope>
