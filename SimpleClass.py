package com.rbs.bdd.infrastructure.soap.api;

import com.rbs.bdd.application.port.in.PaymentValidationPort;
import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.server.endpoint.annotation.Endpoint;
import org.springframework.ws.server.endpoint.annotation.PayloadRoot;
import org.springframework.ws.server.endpoint.annotation.RequestPayload;
import org.springframework.ws.server.endpoint.annotation.ResponsePayload;


/**
 * SOAP endpoint adapter class for handling the `validateArrangementForPayment` operation.
 * It uses Spring WS annotations to route incoming SOAP requests to the appropriate service layer.
 */
@Endpoint
public class PaymentValidationSoapAdapter {

    /**Changes for the request*/

    private static final String NAMESPACE_URI = "http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/";
    private final PaymentValidationPort paymentValidationPort;

    /**
     * Constructor-based injection of the orchestrator that handles business logic.
     *
     * @param paymentValidationPort the orchestrator service
     */
    public PaymentValidationSoapAdapter(PaymentValidationPort paymentValidationPort) {
        this.paymentValidationPort = paymentValidationPort;
    }

    /**
     * Handles the `validateArrangementForPayment` SOAP request.
     * Delegates request processing to the orchestrator which modifies the response message directly.
     *
     * @param request the SOAP request payload
     * @param context the Spring WS message context
     */
    @PayloadRoot(namespace = NAMESPACE_URI, localPart = "validateArrangementForPayment")
    @ResponsePayload
    public void validateArrangementForPayment(@RequestPayload ValidateArrangementForPaymentRequest request,
                                                MessageContext context) {

        WebServiceMessage response = context.getResponse();
        paymentValidationPort.validateArrangementForPayment(request, response);
         }

}




-------------------------------------


package com.rbs.bdd;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;


/**

 * Main Spring boot entry class for the Esp Simulator application.
 * This class bootstraps the spring context and launches the application.

 * Main Spring boot entry class for the Esp Simulator application.
 * This class bootstraps the spring context and launches the application.
 */
@ComponentScan("com.rbs.bdd")
@SpringBootApplication(scanBasePackages = "com.rbs.bdd")
public class EspSimulatorEngine {

    public static void main(String[] args) {
        SpringApplication.run(EspSimulatorEngine.class, args);
    }
}



--------------------------------------


package com.rbs.bdd.infrastructure.config;


import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.application.exception.XsdSchemaLoadingException;
import org.springframework.boot.web.servlet.ServletRegistrationBean;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.ws.config.annotation.EnableWs;
import org.springframework.ws.config.annotation.WsConfigurerAdapter;
import org.springframework.ws.server.EndpointInterceptor;
import org.springframework.ws.soap.server.endpoint.interceptor.PayloadValidatingInterceptor;
import org.springframework.ws.transport.http.MessageDispatcherServlet;
import org.springframework.ws.wsdl.wsdl11.DefaultWsdl11Definition;
import org.springframework.xml.xsd.commons.CommonsXsdSchemaCollection;
import org.springframework.xml.xsd.XsdSchemaCollection;
import java.util.List;

/**
 * Configuration class for setting up Spring WS infrastructure, including schema validation
 * and WSDL exposure. Implements {@link WsConfigurerAdapter}.
 */
@Configuration
@EnableWs
public class SoapWebServiceConfig extends WsConfigurerAdapter {

    /**
     * Registers the Spring WS {@link MessageDispatcherServlet}.
     *
     * @param context Spring ApplicationContext
     * @return ServletRegistrationBean for MessageDispatcherServlet
     */
    @Bean
    public ServletRegistrationBean<MessageDispatcherServlet> messageDispatcherServlet(ApplicationContext context) {
        MessageDispatcherServlet servlet = new MessageDispatcherServlet();
        servlet.setApplicationContext(context);
        servlet.setTransformWsdlLocations(true);
        return new ServletRegistrationBean<>(servlet, "/ws/*");
    }


    /**
     * Adds a schema validating interceptor to validate all incoming requests.
     *
     * @param interceptors list of Spring WS endpoint interceptors
     */
    @Override
    public void addInterceptors(List<EndpointInterceptor> interceptors) {
        SchemaValidationInterceptor validatingInterceptor = new SchemaValidationInterceptor();
        validatingInterceptor.setValidateRequest(true);
        validatingInterceptor.setValidateResponse(false);
        try {
            validatingInterceptor.setXsdSchemaCollection(updateContactXsd());
        } catch (Exception e) {
            throw new XsdSchemaLoadingException("Request  XML Schema Validation failed ",e);
        }
        interceptors.add(validatingInterceptor);
    }


    /**
     * Publishes the WSDL based on the XSD schema.
     *
     * @return DefaultWsdl11Definition for WSDL exposure
     * @throws SchemaValidationException if schema loading fails
     */
    @Bean(name="ArrValidationForPaymentParameters")
    public DefaultWsdl11Definition defaultWsdl11Definition() throws SchemaValidationException {
        DefaultWsdl11Definition wsdl11Definition = new DefaultWsdl11Definition();
        wsdl11Definition.setPortTypeName("IArrValidationForPayment");
        wsdl11Definition.setLocationUri("/ws");
        wsdl11Definition.setTargetNamespace("http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/");
        wsdl11Definition.setSchemaCollection(updateContactXsd());
        return wsdl11Definition;
    }


    /**
     * Loads and inlines the XSD schema used for validating SOAP requests.
     *
     * @return XsdSchemaCollection of all relevant XSDs
     * @throws XsdSchemaLoadingException if schema loading fails
     */
    @Bean
    public XsdSchemaCollection updateContactXsd()  {
        try{
            CommonsXsdSchemaCollection xsd = new CommonsXsdSchemaCollection(new ClassPathResource("xsd/ArrValidationForPaymentParameters.xsd"));
            xsd.setInline(true);
            return xsd;
        }
        catch(Exception e)
        {
            throw new XsdSchemaLoadingException("failed to load XSD schema for SOAP validation",e);
        }

    }
}


---------------------


package com.rbs.bdd.infrastructure.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.server.EndpointInterceptor;

import java.io.ByteArrayOutputStream;
/**
 * Interceptor to log incoming and outgoing SOAP messages for debugging and monitoring.
 * This class logs the full request, response, and fault messages.
 */
public class SoapLoggingInterceptor implements EndpointInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SoapLoggingInterceptor.class);

    /**
     * Logs the incoming SOAP request before it reaches the endpoint.
     *
     * @param messageContext the message context containing the request
     * @param endpoint        the targeted endpoint
     * @return true to continue processing the request
     */
    @Override
    public boolean handleRequest(MessageContext messageContext, Object endpoint) {
        logMessage("SOAP Request", messageContext.getRequest());
        return true;
    }

    /**
     * Logs the outgoing SOAP response after the endpoint returns a result.
     *
     * @param messageContext the message context containing the response
     * @param endpoint        the targeted endpoint
     * @return true to continue processing the response
     */
    @Override
    public boolean handleResponse(MessageContext messageContext, Object endpoint) {
        logMessage("SOAP Response", messageContext.getResponse());
        return true;
    }

    /**
     * Logs the SOAP fault message if an exception occurs during processing.
     *
     * @param messageContext the message context containing the fault
     * @param endpoint        the targeted endpoint
     * @return true to continue processing the fault
     */
    @Override
    public boolean handleFault(MessageContext messageContext, Object endpoint) {
        logMessage("SOAP Fault", messageContext.getResponse());
        return true;
    }

    /**
     * Called after the completion of the message exchange.
     * No action is needed here, but method must be implemented.
     */
    @Override
    public void afterCompletion(MessageContext messageContext, Object endpoint, Exception ex) {
        // No action needed after completion
    }

    /**
     * Helper method to log the SOAP message by writing it to a byte array output stream.
     *
     * @param type    the type of SOAP message (Request, Response, Fault)
     * @param message the WebServiceMessage to be logged
     */
    private void logMessage(String type, org.springframework.ws.WebServiceMessage message) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            message.writeTo(out);  // Serialize the message to an output stream
            logger.info("{}:\n{}", type, out.toString());  // Log the message content
        } catch (Exception e) {
            logger.error("Error logging {} message: {}", type, e.getMessage());
        }
    }
}


-----------


package com.rbs.bdd.infrastructure.config;
import com.rbs.bdd.application.exception.SchemaValidationException;
import jakarta.xml.soap.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.springframework.ws.soap.server.endpoint.interceptor.PayloadValidatingInterceptor;
import org.xml.sax.SAXParseException;




/**
 * Custom interceptor that extends {@link PayloadValidatingInterceptor}
 * to override default SOAP fault response behavior on schema validation failure.
 * <p>
 * If schema validation fails, this interceptor returns a custom SOAP fault message
 * containing a simplified error description extracted from the first SAXParseException.
 * </p>
 */
public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);

    /**
     * Overrides the default schema validation failure handling.
     * Constructs a SOAP fault message containing a custom error string instead of the default stack trace.
     *
     */
    @Override
    public boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors)
            throws SchemaValidationException {

        try {
            WebServiceMessage response = messageContext.getResponse();
            SaajSoapMessage saajMessage = (SaajSoapMessage) response;
            SOAPBody body = saajMessage.getSaajMessage().getSOAPBody();
            body.removeContents();

            String errorMessage = "Schema validation failed: " + (errors.length > 0 ? errors[0].getMessage() : "Unknown error");
            SOAPFactory soapFactory= SOAPFactory.newInstance();
            Name faultCode= soapFactory.createName("Client","",SOAPConstants.URI_NS_SOAP_1_1_ENVELOPE);
            SOAPFault fault= body.addFault(faultCode,errorMessage);
            logger.debug("SOAPFault created: {}", fault.getFaultCode(), fault.getFaultString());
            logger.debug("FaultCode: {}", faultCode);
            logger.warn("Custom schema validation error returned: {}", errorMessage);

        } catch (SOAPException e) {
            logger.error("Error constructing SOAP fault: {}", e.getMessage(), e);
            throw new SchemaValidationException("Failed to write SOAP fault due to schema validation error", e);
        }

        // Stop further processing of this message
        return false;
    }
}


---------------------------


package com.rbs.bdd.domain.enums;


/**
 * Enum representing switching status of the arrangement.
 */
public enum SwitchingStatus {
    SWITCHED("Switched"),
    NOT_SWITCHING("Not Switching");

    private final String value;

    SwitchingStatus(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}


-----------------------


package com.rbs.bdd.domain.enums;

/**
 * Enum representing the result of modulus check validation.
 */
public enum ModulusCheckStatus {
    PASS("Passed"),
    FAILED("Failed");

    private final String value;

    ModulusCheckStatus(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}



-----------------------


package com.rbs.bdd.domain.enums;


/**
 * Enum representing switching status of the arrangement.
 */
public enum SwitchingStatus {
    SWITCHED("Switched"),
    NOT_SWITCHING("Not Switching");

    private final String value;

    SwitchingStatus(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}



------------------------------------------------

package com.rbs.bdd.common;
/**
 * Centralized constants used across the service for validation logic,
 * identifiers, XPath expressions, and configuration values.
 */
public final class ServiceConstants {

    private ServiceConstants() {
        // Prevent instantiation
    }

    // IBAN values
    public static final String IBAN_1 = "GB29NWBK60161331926801";
    public static final String IBAN_2 = "GB82WEST12345698765437";
    public static final String IBAN_3 = "GB94BARC10201530093422";
    public static final String IBAN_4 = "GB33BUKB20201555555567";

    // Code values
    public static final String INTL_BANK_ACCOUNT = "InternationalBankAccountNumber";
    public static final String UK_BASIC_BANK_ACCOUNT = "UKBasicBankAccountNumber";

    // XML/XPath constants
    public static final String RESPONSE_XML_PATH = "static-response/response1.xml";

    public static final String XPATH_TRANSACTION_ID = "//*[local-name()='transactionId']";
    public static final String XPATH_ACCOUNT_STATUS = "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']";
    public static final String XPATH_SWITCHING_STATUS = "//*[local-name()='switchingStatus']/*[local-name()='codeValue']";
    public static final String XPATH_MODULUS_STATUS = "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']";
}



------------------

package com.rbs.bdd.application.service;

import com.rbs.bdd.application.port.out.AccountValidationPort;
import com.rbs.bdd.application.port.in.PaymentValidationPort;
import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.ws.WebServiceMessage;

/**
 * Service class responsible for orchestrating the validation flow of payment arrangement requests.
 * Implements {@link PaymentValidationPort} and delegates schema and business rule validation
 * to the appropriate output port.
 */
@Service
@RequiredArgsConstructor
public class PaymentOrchestrator implements PaymentValidationPort {

    private final AccountValidationPort accountValidationPort;




    /**
     * Entry point for handling the SOAP request. Validates schema and applies business rules.
     *
     * @param request the incoming SOAP request payload
     * @param message the SOAP WebServiceMessage used to write the final response
     */
    @Override
    public void validateArrangementForPayment(ValidateArrangementForPaymentRequest request,WebServiceMessage message) {
        accountValidationPort.validateSchema(request); // automatic validation through interceptors
         accountValidationPort.validateBusinessRules(request,message);
    }

}


---------

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




----------------------


package com.rbs.bdd.application.port.out;

import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;
import org.springframework.ws.WebServiceMessage;

/**
 * Defines the business contract for validating payment accounts.
 * Used by the orchestrator to call schema and business rule validators.
 */
public interface AccountValidationPort {
    /**
     * Performs XSD schema validation of the request. (Currently delegated to Spring WS config.)
     *
     * @param request The SOAP request payload.
     */
    void validateSchema(ValidateArrangementForPaymentRequest request);


    /**
     * Applies business rules on the static response XML based on request content,
     * and writes the final SOAP response directly to the output message.
     *
     * @param request The incoming SOAP request.
     * @param message The WebServiceMessage to write the modified response to.
     */
    void validateBusinessRules(ValidateArrangementForPaymentRequest request,WebServiceMessage message);

     }



--------------------------

package com.rbs.bdd.application.port.in;


import org.springframework.ws.WebServiceMessage;
import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;

/**
 * Entry port for handling SOAP requests related to payment validation.
 * Follows hexagonal architecture's `port in` pattern.
 */
public interface PaymentValidationPort {


    /**
     * Validates a payment arrangement request by delegating to the underlying orchestrator/service.
     *
     * @param request The SOAP request payload.
     * @param message The outgoing WebServiceMessage to be modified and returned.
     */
    void validateArrangementForPayment(ValidateArrangementForPaymentRequest request,WebServiceMessage message);



}



-----------------------------------

package com.rbs.bdd.application.exception;



/**
 * Exception thrown when  the account validation fails during SOAP request processing.
 */
public class AccountValidationException extends RuntimeException {

    /**
     * Constructs a new AccountValidationException with a specific message.
     *
     * @param message the detail message
     */
    public AccountValidationException(String message) {
        super(message);
    }

    /**
     * Constructs a new AccountValidationException with a message and cause.
     *
     * @param message the detail message
     * @param cause the cause of the exception
     */
    public AccountValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}


    ----------------------------------------

package com.rbs.bdd.application.exception;

/**
 * Exception thrown when  the schema validation fails during SOAP request processing.
 */
public class SchemaValidationException extends RuntimeException {

    /**
     * Constructs a new SchemaValidationException with a specific message.
     *
     * @param message the detail message
     */
    public SchemaValidationException(String message) {
        super(message);
    }

    /**
     * Constructs a new SchemaValidationException with a message and cause.
     *
     * @param message the detail message
     * @param cause the cause of the exception
     */
    public SchemaValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}


    ------------------------

package com.rbs.bdd.application.exception;
/**
 * Exception thrown when an error occurs during XML parsing or unmarshalling.
 */
public class XmlParsingException extends RuntimeException {

    /**
     * Constructs a new XmlParsingException with the specified detail message.
     *
     * @param message the detail message explaining the reason for the exception
     */
    public XmlParsingException(String message) {
        super(message);
    }

    /**
     * Constructs a new XmlParsingException with the specified detail message and cause.
     *
     * @param message the detail message
     * @param cause   the cause of the exception (can be retrieved later via {@link #getCause()})
     */
    public XmlParsingException(String message, Throwable cause) {
        super(message, cause);
    }
}


                                                  --------


    package com.rbs.bdd.application.exception;



/**
 * Exception thrown when schema Loading fails during SOAP request processing.
 */
public class XsdSchemaLoadingException extends RuntimeException{

    /**
     * Constructs a new XsdSchemaLoadingException with a specific message.
     *
     * @param message the detail message
     */
    public XsdSchemaLoadingException(String message) {
        super(message);
    }

    /**
     * Constructs a new XsdSchemaLoadingException with a message and cause.
     *
     * @param message the detail message
     * @param cause the cause of the exception
     */
    public XsdSchemaLoadingException(String message,Throwable cause) {
        super(message, cause);
    }
}

---------------------------------------

    Scenario:-

1. Scehma Validation is failed then return :


<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Header/>
   <soap:Body>
      <tns:validateArrangementForPaymentResponse xmlns:tns="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/">
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e31768386a89689bf40f20250529150913864h</transactionId>
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
               <timestamp>2025-05-29T15:09:13+01:00</timestamp>
            </cmdNotifications>
         </exception>
      </tns:validateArrangementForPaymentResponse>
   </soap:Body>
</soap:Envelope>


2. For wrong InternationbankAccountNumber return :-

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v01="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/">
   <soapenv:Header/>
   <soapenv:Body>
      <v01:validateArrangementForPayment>
         <requestHeader>
            <operatingBrand>ALL</operatingBrand>
            <!--Zero or more repetitions:-->
            <requestIds>
               <systemId>RequestID</systemId>
               <transactionId>123456789</transactionId>
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


3. For wrong length of IBAN if less than 22 or more than 22 the below error :-

<soapenv:Envelope xmlns:nsVer="http://com/rbsg/soa/C040PaymentManagement/ArrValidationForPayment/V01/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <nsVer:validateArrangementForPaymentResponse>
         <exception>
            <responseId>
               <systemId>ESP</systemId>
               <transactionId>1alN2edd2e31768386e943585200d20250529152628710h</transactionId>
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
               <returnCode>ERR006</returnCode>
               <category>Error</category>
               <description>Unable to Complete Request</description>
               <timestamp>2025-05-29T15:26:28.765900+01:00</timestamp>
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

