@Bean
public SoapFaultMappingExceptionResolver exceptionResolver() {
    SoapFaultMappingExceptionResolver resolver = new SoapFaultMappingExceptionResolver();
    resolver.setOrder(1);

    Properties errorMappings = new Properties();
    errorMappings.setProperty(SchemaValidationException.class.getName(), SoapFaultDefinition.SERVER.toString());
    resolver.setExceptionMappings(errorMappings);

    SoapFaultDefinition faultDefinition = new SoapFaultDefinition();
    faultDefinition.setFaultCode(SoapFaultDefinition.SERVER);
    faultDefinition.setFaultStringOrReason("Internal Error");
    resolver.setDefaultFault(faultDefinition);

    return resolver;
}



-----

package com.rbs.bdd.infrastructure.soap.interceptor;

import com.rbs.bdd.application.exception.SchemaValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.springframework.ws.soap.server.endpoint.interceptor.PayloadValidatingInterceptor;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXParseException;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
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

import static com.rbs.bdd.common.ServiceConstants.SCHEMA_VALIDATION_ERROR_XML;

/**
 * Intercepts schema validation failures and returns a static custom error SOAP fault
 * with dynamic placeholders replaced and HTTP 500 status.
 */
public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);
    private static final String PLACEHOLDER_TXN = "TXN_ID_PLACEHOLDER";
    private static final String PLACEHOLDER_RESPONSE = "RESPONSE_ID_PLACEHOLDER";

    @Override
    public boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("❌ Schema validation error detected. Returning custom static SOAP error response.");

        try (InputStream staticXml = getClass().getClassLoader().getResourceAsStream(SCHEMA_VALIDATION_ERROR_XML)) {

            if (staticXml == null) {
                logger.error("⚠️ schemaValidationError.xml not found in classpath.");
                return true;
            }

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();

            Document responseDoc = builder.parse(staticXml);

            // Read request to extract txnId/systemId
            WebServiceMessage request = messageContext.getRequest();
            ByteArrayOutputStream reqOut = new ByteArrayOutputStream();
            request.writeTo(reqOut);
            Document requestDoc = builder.parse(new ByteArrayInputStream(reqOut.toByteArray()));

            String requestTxnId = getValueFromRequest(requestDoc, "transactionId");
            String requestSystemId = getValueFromRequest(requestDoc, "systemId");

            // Replace placeholders
            replaceTextNode(responseDoc, PLACEHOLDER_RESPONSE, generateTxnId());
            replaceTextNode(responseDoc, PLACEHOLDER_TXN, requestTxnId != null ? requestTxnId : PLACEHOLDER_TXN);

            // Conditionally remove <transactionId>, <systemId>, <refRequestIds>
            Node refRequestIdsNode = getNode(responseDoc, "refRequestIds");
            if (refRequestIdsNode != null) {
                if (requestTxnId == null) removeNode(refRequestIdsNode, "transactionId");
                if (requestSystemId == null) removeNode(refRequestIdsNode, "systemId");

                if (!refRequestIdsNode.hasChildNodes()) {
                    refRequestIdsNode.getParentNode().removeChild(refRequestIdsNode);
                }
            }

            // Update timestamp
            String ukTime = OffsetDateTime.now(ZoneId.of("Europe/London"))
                    .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
            setXPathValue(responseDoc, "//*[local-name()='timestamp']", ukTime);

            // Write final SOAP response
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(responseDoc), new StreamResult(out));

            SaajSoapMessage response = (SaajSoapMessage) messageContext.getResponse();
            response.getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

            // ❗ Explicitly return HTTP 500 by throwing
            throw new SchemaValidationException("Schema validation failed. Returning SOAP 500 fault.");

        } catch (Exception e) {
            logger.error("⚠️ Error creating custom schema validation SOAP response", e);
            throw new SchemaValidationException("Schema validation failure. Error generating static fault response", e);
        }
    }

    private String getValueFromRequest(Document doc, String tag) {
        NodeList list = doc.getElementsByTagNameNS("*", tag);
        return list.getLength() > 0 ? list.item(0).getTextContent() : null;
    }

    private void replaceTextNode(Document doc, String placeholder, String newValue) {
        NodeList txnNodes = doc.getElementsByTagNameNS("*", "transactionId");
        for (int i = 0; i < txnNodes.getLength(); i++) {
            Node txn = txnNodes.item(i);
            if (placeholder.equals(txn.getTextContent())) {
                txn.setTextContent(newValue);
            }
        }
    }

    private Node getNode(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0) : null;
    }

    private void removeNode(Node parent, String tagName) {
        NodeList children = parent.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            Node child = children.item(i);
            if (tagName.equals(child.getLocalName())) {
                parent.removeChild(child);
                break;
            }
        }
    }

    private void setXPathValue(Document doc, String path, String value) throws Exception {
        XPath xpath = XPathFactory.newInstance().newXPath();
        Node node = (Node) xpath.evaluate(path, doc, XPathConstants.NODE);
        if (node != null) node.setTextContent(value);
    }

    private String generateTxnId() {
        return "1alN" + UUID.randomUUID().toString().replace("-", "") + "h";
    }
}
