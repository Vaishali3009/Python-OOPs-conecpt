package com.rbs.bdd.infrastructure.config;

import com.rbs.bdd.application.exception.SchemaValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
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
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);
    private static final String ERROR_XML = "static-response/schemaValidationError.xml";

    @Override
    protected boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("Schema validation error detected. Generating custom SOAP fault response...");

        try (InputStream xml = getClass().getClassLoader().getResourceAsStream(ERROR_XML)) {
            if (xml == null) {
                logger.error("schemaValidationError.xml not found in resources");
                return true;
            }

            // Build XML documents
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();

            Document responseDoc = builder.parse(xml);
            Document requestDoc = builder.parse(new ByteArrayInputStream(toByteArray(messageContext.getRequest())));

            String requestTxnId = getNodeValue(requestDoc, "transactionId");
            String requestSystemId = getNodeValue(requestDoc, "systemId");

            // Update or remove <refRequestIds>
            Node refRequestIdsNode = getNode(responseDoc, "refRequestIds");

            if (refRequestIdsNode != null) {
                updateOrRemoveChild(refRequestIdsNode, "transactionId", requestTxnId);
                updateOrRemoveChild(refRequestIdsNode, "systemId", requestSystemId);

                // Remove <refRequestIds> if no valid children remain
                if (!refRequestIdsNode.hasChildNodes() || isEmptyTextOnly(refRequestIdsNode)) {
                    Node parent = refRequestIdsNode.getParentNode();
                    parent.removeChild(refRequestIdsNode);
                }
            }

            // Replace responseId -> transactionId
            setNodeValue(responseDoc, "responseId/transactionId", generateTransactionId());

            // Replace timestamp
            String timestamp = OffsetDateTime.now(ZoneId.of("Europe/London"))
                    .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
            setNodeValue(responseDoc, "cmdNotifications/timestamp", timestamp);

            // Write final SOAP response
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(responseDoc), new StreamResult(out));

            SaajSoapMessage saajResponse = (SaajSoapMessage) messageContext.getResponse();
            saajResponse.getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (Exception e) {
            logger.error("Error generating custom schema validation fault", e);
            throw new SchemaValidationException("Failed to generate schema error response", e);
        }

        return false; // Suppress default Spring WS fault
    }

    private byte[] toByteArray(WebServiceMessage message) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        message.writeTo(baos);
        return baos.toByteArray();
    }

    private Node getNode(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0).getParentNode() : null;
    }

    private String getNodeValue(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0).getTextContent() : null;
    }

    private void setNodeValue(Document doc, String path, String value) throws Exception {
        XPath xpath = XPathFactory.newInstance().newXPath();
        Node node = (Node) xpath.evaluate("//*[local-name()='" + path.replace("/", "']/*[local-name()='") + "']",
                doc, XPathConstants.NODE);
        if (node != null) {
            node.setTextContent(value);
        }
    }

    private void updateOrRemoveChild(Node parent, String tagName, String value) {
        NodeList children = parent.getChildNodes();
        boolean found = false;
        for (int i = 0; i < children.getLength(); i++) {
            Node child = children.item(i);
            if (child.getNodeType() == Node.ELEMENT_NODE && tagName.equals(child.getLocalName())) {
                found = true;
                if (value != null) {
                    child.setTextContent(value);
                } else {
                    parent.removeChild(child);
                }
                break;
            }
        }

        // If tag not found and value is not null, add it
        if (!found && value != null) {
            Element newChild = parent.getOwnerDocument().createElementNS(parent.getNamespaceURI(), tagName);
            newChild.setTextContent(value);
            parent.appendChild(newChild);
        }
    }

    private boolean isEmptyTextOnly(Node node) {
        NodeList children = node.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            if (children.item(i).getNodeType() != Node.TEXT_NODE || !children.item(i).getTextContent().trim().isEmpty()) {
                return false;
            }
        }
        return true;
    }

    private String generateTransactionId() {
        return "1alN" + java.util.UUID.randomUUID().toString().replace("-", "") + "h";
    }
}
