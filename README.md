package com.rbs.bdd.infrastructure.config;

import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.common.ServiceConstants;
import jakarta.xml.soap.SOAPException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.springframework.ws.soap.server.endpoint.interceptor.PayloadValidatingInterceptor;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.xml.sax.SAXParseException;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathFactory;

/**
 * Custom interceptor that handles schema validation failures and replaces the
 * SOAP response with a static XML error file customized with request ID and timestamp.
 */
public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);

    @Override
    protected boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("Schema validation error detected. Generating custom SOAP fault response.");

        try (InputStream xml = getClass().getClassLoader()
                .getResourceAsStream(ServiceConstants.SCHEMA_VALIDATION_ERROR_XML_PATH)) {

            if (xml == null) {
                logger.error("schemaValidationError.xml not found in resources");
                return true; // fallback to default behavior
            }

            // Load and parse static XML
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);

            // Modify: refRequestIds > transactionId
            XPath xpath = XPathFactory.newInstance().newXPath();
            Node refTxnIdNode = (Node) xpath.evaluate("//*[local-name()='refRequestIds']/*[local-name()='transactionId']",
                    doc, XPathConstants.NODE);
            String incomingTxnId = extractTransactionIdFromRequest(messageContext);
            if (refTxnIdNode != null && incomingTxnId != null) {
                refTxnIdNode.setTextContent(incomingTxnId);
            }

            // Modify: responseId > transactionId
            Node responseTxnIdNode = (Node) xpath.evaluate("//*[local-name()='responseId']/*[local-name()='transactionId']",
                    doc, XPathConstants.NODE);
            if (responseTxnIdNode != null) {
                responseTxnIdNode.setTextContent(generateTransactionId());
            }

            // Modify: timestamp
            Node timestampNode = (Node) xpath.evaluate("//*[local-name()='timestamp']", doc, XPathConstants.NODE);
            if (timestampNode != null) {
                timestampNode.setTextContent(getCurrentUKTimestamp());
            }

            // Write modified XML to SOAP response
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            WebServiceMessage response = messageContext.getResponse();
            ((SaajSoapMessage) response).getSaajMessage().getSOAPPart()
                    .setContent(new javax.xml.transform.stream.StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (Exception e) {
            logger.error("Failed to generate custom schema validation fault response", e);
            throw new SchemaValidationException("Failed to generate schema validation fault", e);
        }

        return false; // prevent default SOAP Fault
    }

    private String extractTransactionIdFromRequest(MessageContext messageContext) {
        try {
            SaajSoapMessage request = (SaajSoapMessage) messageContext.getRequest();
            Document doc = request.getSaajMessage().getSOAPPart().getEnvelope().getBody();
            XPath xpath = XPathFactory.newInstance().newXPath();
            Node txnIdNode = (Node) xpath.evaluate("//*[local-name()='requestIds']/*[local-name()='transactionId']",
                    doc, XPathConstants.NODE);
            return txnIdNode != null ? txnIdNode.getTextContent() : null;
        } catch (Exception e) {
            logger.error("Could not extract transactionId from request", e);
            return null;
        }
    }

    private String generateTransactionId() {
        return "1alN" + UUID.randomUUID().toString().replace("-", "") + "h";
    }

    private String getCurrentUKTimestamp() {
        ZonedDateTime now = ZonedDateTime.now(java.time.ZoneId.of("Europe/London"));
        return now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX"));
    }
}
