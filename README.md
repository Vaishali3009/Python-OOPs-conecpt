package com.rbs.bdd.infrastructure.config;

import com.rbs.bdd.common.ServiceConstants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.server.endpoint.interceptor.PayloadValidatingInterceptor;
import org.w3c.dom.*;
import org.xml.sax.SAXParseException;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);

    @Override
    protected boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("Schema validation error detected. Generating custom SOAP fault response.");

        try (InputStream xml = getClass().getClassLoader().getResourceAsStream(ServiceConstants.SCHEMA_VALIDATION_ERROR_XML)) {
            if (xml == null) {
                logger.error("schemaValidationError.xml not found in resources");
                return true;
            }

            // Parse error XML
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);

            // Extract request content
            WebServiceMessage request = messageContext.getRequest();
            Document requestDoc = builder.parse(request.getPayloadSource().getInputStream());

            String requestTxnId = getNodeValue(requestDoc, "transactionId");
            String requestSystemId = getNodeValue(requestDoc, "systemId");

            // Update or remove <refRequestIds>/<transactionId> and <systemId>
            Node refRequestIdsNode = getNode(doc, "refRequestIds");
            if (refRequestIdsNode != null) {
                updateOrRemoveChild(refRequestIdsNode, "transactionId", requestTxnId);
                updateOrRemoveChild(refRequestIdsNode, "systemId", requestSystemId);

                if (!refRequestIdsNode.hasChildNodes()) {
                    refRequestIdsNode.getParentNode().removeChild(refRequestIdsNode);
                }
            }

            // Set new random transactionId in <responseId>
            String newTxnId = "1alN" + java.util.UUID.randomUUID().toString().replace("-", "") + "h";
            setNodeValue(doc, "responseId/transactionId", newTxnId);

            // Update timestamp
            String timestamp = OffsetDateTime.now(ZoneId.of("Europe/London"))
                    .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
            setNodeValue(doc, "cmdNotifications/timestamp", timestamp);

            // Write modified document to response
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));
            messageContext.getResponse().setPayload(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (Exception e) {
            logger.error("Error generating custom schema validation response", e);
            return true;
        }

        return false; // block default Spring fault
    }

    private String getNodeValue(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0).getTextContent() : null;
    }

    private Node getNode(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0) : null;
    }

    private void setNodeValue(Document doc, String path, String value) {
        NodeList nodes = doc.getElementsByTagNameNS("*", path.substring(path.lastIndexOf("/") + 1));
        if (nodes.getLength() > 0) {
            nodes.item(0).setTextContent(value);
        }
    }

    private void updateOrRemoveChild(Node parent, String tagName, String value) {
        NodeList children = ((Element) parent).getElementsByTagNameNS("*", tagName);
        if (value == null || value.isBlank()) {
            if (children.getLength() > 0) {
                parent.removeChild(children.item(0));
            }
        } else {
            if (children.getLength() > 0) {
                children.item(0).setTextContent(value);
            }
        }
    }
}
