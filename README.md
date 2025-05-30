package com.rbs.bdd.infrastructure.config;

import com.rbs.bdd.common.ServiceConstants;
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
import javax.xml.soap.SOAPException;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * Intercepts schema validation failures and replaces the SOAP response with a custom static fault response.
 */
public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);
    private static final String PLACEHOLDER = "TXN_ID_PLACEHOLDER";

    @Override
    protected boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("Schema validation error detected. Generating custom SOAP fault response...");

        try (InputStream xml = getClass().getClassLoader().getResourceAsStream("static-response/schemaValidationError.xml")) {
            if (xml == null) {
                logger.error("schemaValidationError.xml not found in resources");
                return true;
            }

            // Load static error XML as DOM
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);

            // Prepare XPath
            XPath xpath = XPathFactory.newInstance().newXPath();

            // Extract transactionId from incoming request (XPath to original request's field)
            WebServiceMessage requestMessage = messageContext.getRequest();
            ByteArrayOutputStream requestOut = new ByteArrayOutputStream();
            requestMessage.writeTo(requestOut);
            Document requestDoc = builder.parse(new ByteArrayInputStream(requestOut.toByteArray()));

            String requestTxnId = xpath.evaluate("//*[local-name()='transactionId']", requestDoc);
            if (requestTxnId == null || requestTxnId.isBlank()) {
                requestTxnId = "UNKNOWN_TXN";
            }

            // Modify the static XML: update responseId->transactionId, refRequestIds->transactionId, timestamp
            String generatedTxnId = "1alN" + UUID.randomUUID().toString().replace("-", "").substring(0, 28) + "h";
            String ukTimestamp = OffsetDateTime.now(ZoneId.of("Europe/London"))
                    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX"));

            setNodeText(xpath, doc, "//*[local-name()='responseId']/*[local-name()='transactionId']", generatedTxnId);
            setNodeText(xpath, doc, "//*[local-name()='refRequestIds']/*[local-name()='transactionId']", requestTxnId);
            setNodeText(xpath, doc, "//*[local-name()='timestamp']", ukTimestamp);

            // Write back the modified XML to the response
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            DOMSource domSource = new DOMSource(doc);
            StreamResult streamResult = new StreamResult(out);
            javax.xml.transform.TransformerFactory.newInstance().newTransformer().transform(domSource, streamResult);

            SaajSoapMessage saajMessage = (SaajSoapMessage) messageContext.getResponse();
            saajMessage.getSaajMessage().getSOAPPart().setContent(
                    new StreamSource(new ByteArrayInputStream(out.toByteArray()))
            );

        } catch (Exception e) {
            logger.error("Failed to handle schema validation error", e);
            return true; // fallback to default
        }

        return false; // stop further processing
    }

    /**
     * Utility to set node text via XPath.
     */
    private void setNodeText(XPath xpath, Document doc, String expression, String value) throws Exception {
        Node node = (Node) xpath.evaluate(expression, doc, XPathConstants.NODE);
        if (node != null) {
            node.setTextContent(value);
        } else {
            logger.warn("XPath not found: " + expression);
        }
    }
}
