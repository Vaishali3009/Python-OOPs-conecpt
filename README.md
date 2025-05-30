package com.rbs.bdd.infrastructure.soap.interceptor;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.server.EndpointInterceptor;
import org.springframework.ws.soap.SoapMessage;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.w3c.dom.Document;
import org.w3c.dom.Node;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * Interceptor to handle schema validation failures by returning a custom SOAP error response.
 */
public class SchemaValidationInterceptor implements EndpointInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);
    private static final String ERROR_XML_PATH = "error-responses/schemaValidationError.xml";
    private static final String XPATH_TRANSACTION_ID = "//*[local-name()='refRequestIds']/*[local-name()='transactionId']";
    private static final String XPATH_RESPONSE_ID = "//*[local-name()='responseId']";
    private static final String XPATH_TIMESTAMP = "//*[local-name()='timestamp']";

    @Override
    public boolean handleRequest(MessageContext messageContext, Object endpoint) {
        return true;
    }

    @Override
    public boolean handleResponse(MessageContext messageContext, Object endpoint) {
        return true;
    }

    @Override
    public boolean handleFault(MessageContext messageContext, Object endpoint) {
        try {
            // Load the static error response XML
            ClassPathResource resource = new ClassPathResource(ERROR_XML_PATH);
            byte[] bytes = resource.getInputStream().readAllBytes();

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(new ByteArrayInputStream(bytes));

            // Modify the document
            setNodeValue(doc, XPATH_TRANSACTION_ID, generateTransactionId());
            setNodeValue(doc, XPATH_RESPONSE_ID, generateTransactionId());
            setNodeValue(doc, XPATH_TIMESTAMP, getCurrentTimestamp());

            // Convert back to SOAP message
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            SaajSoapMessage response = (SaajSoapMessage) messageContext.getResponse();
            response.getSaajMessage().getSOAPPart()
                    .setContent(new DOMSource(builder.parse(new ByteArrayInputStream(out.toByteArray()))));

        } catch (Exception ex) {
            logger.error("Error generating custom SOAP fault response: {}", ex.getMessage(), ex);
        }

        return false; // Stop further processing
    }

    @Override
    public void afterCompletion(MessageContext messageContext, Object endpoint, Exception ex) {
        // No-op
    }

    /**
     * Updates a node's text content by XPath.
     */
    private void setNodeValue(Document doc, String xpathExpr, String value) throws Exception {
        Node node = javax.xml.xpath.XPathFactory.newInstance().newXPath()
                .evaluate(xpathExpr, doc, javax.xml.xpath.XPathConstants.NODE) instanceof Node n ? n : null;
        if (node != null) {
            node.setTextContent(value);
        }
    }

    /**
     * Generates a random transaction ID for responseId or transactionId fields.
     */
    private String generateTransactionId() {
        return "1alN2edd" + UUID.randomUUID().toString().replace("-", "") + "h";
    }

    /**
     * Gets the current timestamp in UK time zone with required format.
     */
    private String getCurrentTimestamp() {
        return ZonedDateTime.now(java.time.ZoneId.of("Europe/London"))
                .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    }
}




------
public class ServiceConstants {
    public static final String SCHEMA_VALIDATION_ERROR_XML = "error-response/schemaValidationError.xml";

    public static final String XPATH_FAULT_TRANSACTION_ID = "//*[local-name()='refRequestIds']/*[local-name()='transactionId']";
    public static final String XPATH_FAULT_RESPONSE_ID = "//*[local-name()='responseId']";
    public static final String XPATH_FAULT_TIMESTAMP = "//*[local-name()='timestamp']";
}

