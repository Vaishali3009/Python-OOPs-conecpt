package com.rbs.bdd.infrastructure.config;

import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.common.ServiceConstants;
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

/**
 * Intercepts schema validation errors and returns custom SOAP response from static XML.
 */
public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);

    @Override
    protected boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("Schema validation error detected. Generating custom SOAP fault response...");

        try (InputStream xml = getClass().getClassLoader().getResourceAsStream("static-response/schemaValidationError.xml")) {
            if (xml == null) {
                logger.error("schemaValidationError.xml not found in resources");
                return true; // fallback to default behavior
            }

            // Parse static XML
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);

            // Parse request
            WebServiceMessage request = messageContext.getRequest();
            Document requestDoc = builder.parse(new ByteArrayInputStream(toByteArray(request)));

            String requestTxnId = getNodeValue(requestDoc, "transactionId");
            String requestSystemId = getNodeValue(requestDoc, "systemId");

            // refRequestIds logic
            Node refRequestIdsNode = getNode(doc, "refRequestIds");
            if (refRequestIdsNode != null) {
                if (requestTxnId != null) {
                    updateOrRemoveChild(refRequestIdsNode, "transactionId", requestTxnId);
                } else {
                    removeChild(refRequestIdsNode, "transactionId");
                }

                if (requestSystemId != null) {
                    updateOrRemoveChild(refRequestIdsNode, "systemId", requestSystemId);
                } else {
                    removeChild(refRequestIdsNode, "systemId");
                }

                if (!refRequestIdsNode.hasChildNodes()) {
                    refRequestIdsNode.getParentNode().removeChild(refRequestIdsNode);
                }
            }

            // Set timestamp
            String timestamp = OffsetDateTime.now(ZoneId.of("Europe/London"))
                    .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
            setNodeValue(doc, "cmdNotifications/timestamp", timestamp);

            // Transform DOM to SOAP
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            SaajSoapMessage saajResponse = (SaajSoapMessage) messageContext.getResponse();
            saajResponse.getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (Exception e) {
            logger.error("Error generating custom schema validation fault", e);
            throw new SchemaValidationException("Failed to generate schema error response", e);
        }

        return false; // prevent default Spring fault
    }

    // Convert WebServiceMessage to byte[]
    private byte[] toByteArray(WebServiceMessage message) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        message.writeTo(baos);
        return baos.toByteArray();
    }

    // Get node by local name
    private Node getNode(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0).getParentNode() : null;
    }

    // Get value of node
    private String getNodeValue(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0).getTextContent() : null;
    }

    // Set or update text content
    private void setNodeValue(Document doc, String path, String value) throws Exception {
        XPath xpath = XPathFactory.newInstance().newXPath();
        Node node = (Node) xpath.evaluate("//*[local-name()='" + path.replace("/", "']/*[local-name()='") + "']",
                doc, XPathConstants.NODE);
        if (node != null) {
            node.setTextContent(value);
        }
    }

    // Update or add child
    private void updateOrRemoveChild(Node parent, String tagName, String value) {
        NodeList children = parent.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            Node child = children.item(i);
            if (child.getLocalName() != null && child.getLocalName().equals(tagName)) {
                child.setTextContent(value);
                return;
            }
        }

        // If tag not found, add new
        Node newChild = parent.getOwnerDocument().createElementNS(parent.getNamespaceURI(), tagName);
        newChild.setTextContent(value);
        parent.appendChild(newChild);
    }

    // Remove child node
    private void removeChild(Node parent, String tagName) {
        NodeList children = parent.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            Node child = children.item(i);
            if (child.getLocalName() != null && child.getLocalName().equals(tagName)) {
                parent.removeChild(child);
                break;
            }
        }
    }
}
