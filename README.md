1. If the request transactionId is not present or the tag is missing then generate :-

Response :-

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v01="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/">
   <soapenv:Header/>
   <soapenv:Body>
      <v01:validateArrangementForPayment>
         <requestHeader>
            <operatingBrand>ALL</operatingBrand>
            <!--Zero or more repetitions:-->
            <requestIds>
               <systemId>RequestID</systemId>
               <transactionId>123456720</transactionId>
            </requestIds>
            <cmdType>Request</cmdType>
         </requestHeader>
         <arrangementIdentifier>
            <identifier>GB29NWBK60161331926801</identifier>
            <context>
               <schemeName>ArrangementEnterpriseIdType</schemeName>
               <codeValue>InternationalBankAccountNumber</codeValue>
            </context>
         </arrangementIdentifier>
      </v01:validateArrangementForPayment>
   </soapenv:Body>
</soapenv:Envelope>


-----------------------------------
2. If the length of IBAn account is less than or greater tha 22 characters then generate the error :-

<soapenv:Envelope xmlns:nsVer="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <nsVer:validateArrangementForPaymentResponse>
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e317683adfb935bb63ad20250531115345930h</transactionId>
            </responseId>
            <refRequestIds>
               <systemId>RequestID</systemId>
               <transactionId>123456720</transactionId>
            </refRequestIds>
            <operatingBrand>ALL</operatingBrand>
            <serviceName>ArrValidationForPayment</serviceName>
            <operationName>validateArrangementForPayment</operationName>
            <cmdStatus>Failed</cmdStatus>
            <cmdNotifications>
               <returnCode>ERR006</returnCode>
               <category>Error</category>
               <description>Unable to Complete Request</description>
               <timestamp>2025-05-31T11:53:46.011660+01:00</timestamp>
               <systemNotifications>
                  <returnCode>0013</returnCode>
                  <category>Error</category>
                  <description>Length of IBAN is Invalid</description>
                  <processingId>
                     <systemId>PMP</systemId>
                  </processingId>
               </systemNotifications>
            </cmdNotifications>
         </exception>
      </nsVer:validateArrangementForPaymentResponse>
   </soapenv:Body>
</soapenv:Envelope>

--------------------------------------------


3. For Wrong Account Number(If Account is not found ) :-
 
Response :- <soapenv:Envelope xmlns:nsVer="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <nsVer:validateArrangementForPaymentResponse>
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e317683adef135bb59bd20250531115025858h</transactionId>
            </responseId>
            <refRequestIds>
               <systemId>RequestID</systemId>
               <transactionId>123456720</transactionId>
            </refRequestIds>
            <operatingBrand>ALL</operatingBrand>
            <serviceName>ArrValidationForPayment</serviceName>
            <operationName>validateArrangementForPayment</operationName>
            <cmdStatus>Failed</cmdStatus>
            <cmdNotifications>
               <returnCode>ERR006</returnCode>
               <category>Error</category>
               <description>Unable to Complete Request</description>
               <timestamp>2025-05-31T11:50:25.917704+01:00</timestamp>
               <systemNotifications>
                  <returnCode>0020</returnCode>
                  <category>Error</category>
                  <description>MOD97 failure for the IBAN</description>
                  <processingId>
                     <systemId>PMP</systemId>
                  </processingId>
               </systemNotifications>
            </cmdNotifications>
         </exception>
      </nsVer:validateArrangementForPaymentResponse>
   </soapenv:Body>
</soapenv:Envelope>

---------------------------------

4. If the identifier starts with GB and codeValue isnot  InternationalBankAccountNumber then return 

<soapenv:Envelope xmlns:outNS="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <outNS:validateArrangementForPaymentResponse>
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e317683b1b7e35be562d20250531160846989h</transactionId>
            </responseId>
            <refRequestIds>
               <systemId>RequestID</systemId>
               <transactionId>123456720</transactionId>
            </refRequestIds>
            <operatingBrand>ALL</operatingBrand>
            <serviceName>ArrValidationForPayment</serviceName>
            <operationName>validateArrangementForPayment</operationName>
            <cmdStatus>Failed</cmdStatus>
            <cmdNotifications>
               <returnCode>ERR006</returnCode>
               <category>Error</category>
               <description>Unable To Complete Request</description>
               <timestamp>2025-05-31T16:08:47.027129+01:00</timestamp>
               <systemNotifications>
                  <category>Error</category>
                  <description>500|Service GRPUB.OA_GET_SORTCODE_DETAILS.(OA2.2105271236) execution failed due to SQLCODE=-551 SQLSTATE=42501, CPOA001G DOES NOT HAVE THE PRIVILEGE TO PERFORM OPERATION EXECUTE PACKAGE ON OBJECT GRPUB.OA_GET_SORTCODE_DETAILS. Error Location:DSNLJACC:35</description>
                  <processingId>
                     <systemId>BPP</systemId>
                  </processingId>
               </systemNotifications>
            </cmdNotifications>
         </exception>
      </outNS:validateArrangementForPaymentResponse>
   </soapenv:Body>
</soapenv:Envelope>







--------------------------------------


package com.rbs.bdd.application.service;

import com.rbs.bdd.application.exception.AccountValidationException;
import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.application.exception.XmlParsingException;
import com.rbs.bdd.application.port.out.AccountValidationPort;
import com.rbs.bdd.common.ServiceConstants;
import com.rbs.bdd.domain.enums.AccountStatus;
import com.rbs.bdd.domain.enums.ModulusCheckStatus;
import com.rbs.bdd.domain.enums.SwitchingStatus;
import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.Optional;
import java.util.UUID;

/**
 * Validates the SOAP request schema and applies business logic
 * to return a transformed static SOAP response using DOM and XPath.
 *
 * Implements {@link AccountValidationPort} as part of the hexagonal architecture.
 * Uses account identifier and code type to determine if the account should be considered
 * valid, and if so, transforms a static response template by injecting dynamic fields.
 */
@Service
@RequiredArgsConstructor
public class AccountValidationService implements AccountValidationPort {

    private static final Logger logger = LoggerFactory.getLogger(AccountValidationService.class);

    /**
     * Validates the XSD schema. This is a placeholder as Spring WS performs schema validation via interceptors.
     *
     * @param request the incoming request to be validated
     */
    @Override
    public void validateSchema(ValidateArrangementForPaymentRequest request) {
        logger.info("Schema validation completed (handled by Spring WS interceptor)");
    }

    /**
     * Applies business rules and transforms the SOAP response using DOM + XPath.
     * If account conditions match, replaces values in the response. Otherwise, throws a SOAP fault.
     *
     * @param request the incoming SOAP request
     * @param message the outgoing response message to populate
     */
    @Override
    public void validateBusinessRules(ValidateArrangementForPaymentRequest request, WebServiceMessage message) {
        try (InputStream xml = getClass().getClassLoader().getResourceAsStream(ServiceConstants.RESPONSE_XML_PATH)) {
            if (xml == null) throw new SchemaValidationException("Static response XML not found");

            DocumentBuilderFactory factory = createSecureDocumentBuilderFactory();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);
            XPath xpath = XPathFactory.newInstance().newXPath();

            RequestParams params = extractRequestDetails(request);
            logger.debug("Request:- Account no - " +params.identifier);
            logger.debug("Request:- Account Type - " +params.codeValue);
            logger.debug("Number of Digits in account no  : "+ params.numberOfDigits);
            ResponseConfig config = determineMatchingConfig(params)
                    .orElseThrow(() -> new AccountValidationException("Account Validation failed: account not found"));
            logger.info("Account Type: "+config.status);
            logger.info("Account Switching Type: "+config.switching());
            logger.info("Account Modulus : "+config.modulus());
            updateResponseDocument(doc, xpath, config);

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            TransformerFactory transformerFactory = TransformerFactory.newInstance();
            transformerFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD,"");
            transformerFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET,"");
            Transformer transformer = transformerFactory.newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));
            ((SaajSoapMessage) message).getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (AccountValidationException e) {
            logger.error("Validation exception: {}", e.getMessage(), e);
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error during response generation: {}", e.getMessage(), e);
            throw new AccountValidationException("Account validation failed", e);
        }
    }

    /**
     * Extracts identifier, code value, and number of digits from the request payload.
     *
     * @param request SOAP request
     * @return parsed request params
     */
    private RequestParams extractRequestDetails(ValidateArrangementForPaymentRequest request) {
        String identifier = request.getArrangementIdentifier().getIdentifier();
        String codeValue = request.getArrangementIdentifier().getContext().getCodeValue();
        int length = identifier != null ? identifier.length() : 0;
        return new RequestParams(identifier, codeValue, length);
    }

    /**
     * Determines the appropriate response based on the incoming request fields.
     *
     * @param p request parameter holder
     * @return optional config to update the response with
     */
    private Optional<ResponseConfig> determineMatchingConfig(RequestParams p) {
        ResponseConfig result=null;

      if (isMatch(p, ServiceConstants.IBAN_1) ){
          logger.info("Account is Domestic-Restricted, Switched, and modulus is passed");
          result= new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS);
      }
      else if( isMatch(p, ServiceConstants.IBAN_2) )
      {
          logger.info("Account is Domestic-Restricted, NotSwitching, and modulus is passed");
          result= new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.PASS);
      }
      else if(isMatch(p, ServiceConstants.IBAN_3))
      {
          logger.info("Account is Domestic-Unrestricted, Switched, and modulus is passed");
          result = new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS);
      }
      else if(isMatch(p, ServiceConstants.IBAN_4))
      {
          logger.info("Account is Domestic-Unrestricted, NotSwitching, and modulus is failed");
          result= new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.FAILED);
      }
      else{
          logger.info("Account Not Found");
        }
      return  Optional.ofNullable(result);
    }

    /**
     * Checks if a request matches a given IBAN rule.
     *
     * @param p    the request parameters
     * @param iban the full IBAN to match against
     * @return true if matches either full IBAN or UK version
     */
    private boolean isMatch(RequestParams p, String iban) {
        if(iban==null || p==null) return false;

        String ukEquivalent = extractLast14Digits(iban);
        if(ukEquivalent==null) return false;
        return (p.numberOfDigits() == 22 && ServiceConstants.INTL_BANK_ACCOUNT.equals(p.codeValue()) && iban.equals(p.identifier()))
                || (p.numberOfDigits() == 14 && ServiceConstants.UK_BASIC_BANK_ACCOUNT.equals(p.codeValue()) && ukEquivalent.equals(p.identifier()));
    }

    /**
     * Extracts the last 14 characters from an IBAN string.
     *
     * @param value input string (typically an IBAN)
     * @return last 14 characters or entire input if shorter
     */
    private String extractLast14Digits(String value) {
        return value != null && value.length() >= 14 ? value.substring(value.length() - 14) : value;
    }

    /**
     * Updates response document nodes using XPath with values from business logic.
     *
     * @param doc    the DOM document to modify
     * @param xpath  XPath engine
     * @param config the new values to set
     * @throws XPathExpressionException if XPath fails
     */
    private void updateResponseDocument(Document doc, XPath xpath, ResponseConfig config) throws XPathExpressionException {
        set(xpath, doc, ServiceConstants.XPATH_TRANSACTION_ID, generateTransactionId());
        set(xpath, doc, ServiceConstants.XPATH_ACCOUNT_STATUS, config.status().getValue());
        set(xpath, doc, ServiceConstants.XPATH_SWITCHING_STATUS, config.switching().getValue());
        set(xpath, doc, ServiceConstants.XPATH_MODULUS_STATUS, config.modulus().getValue());
    }

    /**
     * Updates a DOM node's value using XPath.
     *
     * @param xpath XPath engine
     * @param doc   DOM document
     * @param expr  XPath expression
     * @param value value to assign
     * @throws XPathExpressionException if node is not found
     */
    private void set(XPath xpath, Document doc, String expr, String value) throws XPathExpressionException {
        Node node = (Node) xpath.evaluate(expr, doc, XPathConstants.NODE);
        if (node != null) node.setTextContent(value);
    }

    /**
     * Generates a unique transaction ID used in the response.
     *
     * @return UUID-based transaction ID
     */
    private String generateTransactionId() {
        return "3flS" + UUID.randomUUID().toString().replace("-", "") + "h";
    }


    /**
     * Immutable record representing extracted request values.
     * This encapsulates the input fields required to determine which account configuration applies.
     * @param identifier      the IBAN or UK account number
     * @param codeValue       the code type (e.g., InternationalBankAccountNumber)
     * @param numberOfDigits  number of characters in the identifier
     */
    @SuppressWarnings("unused")
    private record RequestParams(String identifier, String codeValue, int numberOfDigits) {
        //This record act as data carrier between schema parsing and business rule engine

    }

    /**
     * Immutable record representing business rule results to apply in the response.
     * This holds the mapped response values after matching input against business rules.
     * @param status    the account status
     * @param switching the switching status
     * @param modulus   the modulus check result
     */

    @SuppressWarnings("unused")
    private record ResponseConfig(AccountStatus status, SwitchingStatus switching, ModulusCheckStatus modulus) {
    // Acts as a container for response attributes derived from business rules.

}
    /**
     * Creates a secure, namespace-aware {@link DocumentBuilderFactory} instance configured
     * to protect against XML External Entity (XXE) attacks and unsafe XML parsing behavior.
     *
     * @return a secure {@link DocumentBuilderFactory}
     * @throws ParserConfigurationException if factory features cannot be set
     */
    private DocumentBuilderFactory createSecureDocumentBuilderFactory() throws  ParserConfigurationException {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
        factory.setXIncludeAware(false);
        factory.setExpandEntityReferences(false);
        return factory;
    }
}

