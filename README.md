package com.rbs.bdd.infrastructure.config;


import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.application.exception.XsdSchemaLoadingException;
import com.rbs.bdd.infrastructure.soap.interceptor.SchemaValidationInterceptor;
import org.springframework.boot.web.servlet.ServletRegistrationBean;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.ws.config.annotation.EnableWs;
import org.springframework.ws.config.annotation.WsConfigurerAdapter;
import org.springframework.ws.server.EndpointInterceptor;
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
    @Bean
    public SoapFaultMappingExceptionResolver exceptionResolver() {
        SoapFaultMappingExceptionResolver resolver = new SoapFaultMappingExceptionResolver();
        resolver.setOrder(1); // High priority

        // Map all exceptions to SERVER fault
        Properties errorMappings = new Properties();
        errorMappings.setProperty(Exception.class.getName(), SoapFaultDefinition.SERVER.toString());
        resolver.setExceptionMappings(errorMappings);

        // Set default fault message
        SoapFaultDefinition defaultFault = new SoapFaultDefinition();
        defaultFault.setFaultCode(SoapFaultDefinition.SERVER);
        defaultFault.setFaultStringOrReason("Internal Error");
        resolver.setDefaultFault(defaultFault);

        return resolver;
    }**/

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




--------------------------------

package com.rbs.bdd.infrastructure.soap.interceptor;

import com.rbs.bdd.application.exception.SchemaValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.client.WebServiceClientException;
import org.springframework.ws.context.MessageContext;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.springframework.ws.soap.server.endpoint.interceptor.PayloadValidatingInterceptor;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

import static com.rbs.bdd.common.ServiceConstants.SCHEMA_VALIDATION_ERROR_XML;

/**
 * Intercepts schema validation failures and replaces the SOAP response with a custom static XML response.
 */
public class SchemaValidationInterceptor extends PayloadValidatingInterceptor {

    private static final Logger logger = LoggerFactory.getLogger(SchemaValidationInterceptor.class);
    private static final String PLACEHOLDER_TXN = "TXN_ID_PLACEHOLDER";
    private static final String PLACEHOLDER_RESPONSE = "RESPONSE_ID_PLACEHOLDER";


    @Override
    public boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
        logger.warn("Schema validation error detected. Replacing response using static schemaValidationError.xml");

        try (InputStream staticXml = getClass().getClassLoader()
                .getResourceAsStream(SCHEMA_VALIDATION_ERROR_XML)) {

            if (staticXml == null) {
                logger.error("Static schema validation error file not found in resources.");
                return true; // fallback to default Spring fault
            }

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();

            // Load error response
            Document doc = builder.parse(staticXml);

            // Load original request
            WebServiceMessage request = messageContext.getRequest();
            ByteArrayOutputStream reqOut = new ByteArrayOutputStream();
            request.writeTo(reqOut);
            Document requestDoc = builder.parse(new ByteArrayInputStream(reqOut.toByteArray()));

            String requestTxnId = getValueFromRequest(requestDoc, "transactionId");
            String requestSystemId = getValueFromRequest(requestDoc, "systemId");

            // Update placeholders in response
            replaceTextNode(doc, PLACEHOLDER_RESPONSE, generateTxnId());
            replaceTextNode(doc, PLACEHOLDER_TXN, requestTxnId != null ? requestTxnId : PLACEHOLDER_TXN);

            // Handle optional requestId tags
            Node refRequestIdsNode = getNode(doc, "refRequestIds");

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
            setXPathValue(doc, "//*[local-name()='timestamp']", ukTime);

            // Write final response
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            SaajSoapMessage soapResponse = (SaajSoapMessage) messageContext.getResponse();
            soapResponse.getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (Exception e) {
            logger.error("Error creating custom schema validation response", e);
            throw new SchemaValidationException("Failed to generate custom schema validation response", e);
        }

        return false; // prevent default SOAP fault
    }

    private String generateTxnId() {
        return "1alN" + UUID.randomUUID().toString().replace("-", "") + "h";
    }

    private String getValueFromRequest(Document doc, String tag) {
        NodeList list = doc.getElementsByTagNameNS("*", tag);
        return list.getLength() > 0 ? list.item(0).getTextContent() : null;
    }

    private Node getNode(Document doc, String localName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", localName);
        return nodes.getLength() > 0 ? nodes.item(0) : null;
    }

    private void replaceTextNode(Document doc, String placeholder, String newValue) {
        NodeList nodes = doc.getElementsByTagNameNS("*", "transactionId");
        for (int i = 0; i < nodes.getLength(); i++) {
            Node txn = nodes.item(i);
            if (placeholder.equals(txn.getTextContent())) {
                txn.setTextContent(newValue);
            }
        }

        NodeList responseNodes = doc.getElementsByTagNameNS("*", "transactionId");
        for (int i = 0; i < responseNodes.getLength(); i++) {
            Node txn = responseNodes.item(i);
            if (placeholder.equals(txn.getTextContent())) {
                txn.setTextContent(newValue);
            }
        }
    }

    private void setXPathValue(Document doc, String path, String value) throws Exception {
        XPath xpath = XPathFactory.newInstance().newXPath();
        Node node = (Node) xpath.evaluate(path, doc, XPathConstants.NODE);
        if (node != null) node.setTextContent(value);
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
}


