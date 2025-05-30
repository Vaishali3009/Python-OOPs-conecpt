@Override
protected boolean handleRequestValidationErrors(MessageContext messageContext, SAXParseException[] errors) {
    logger.warn("Schema validation error detected. Generating custom SOAP fault response.");

    try (InputStream xml = getClass().getClassLoader().getResourceAsStream(ServiceConstants.SCHEMA_VALIDATION_ERROR_XML)) {

        if (xml == null) {
            logger.error("schemaValidationError.xml not found in resources");
            return true;
        }

        // Parse static error XML
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.parse(xml);

        // Extract transactionId from request
        SaajSoapMessage requestMessage = (SaajSoapMessage) messageContext.getRequest();
        SOAPMessage soapRequest = requestMessage.getSaajMessage();
        SOAPBody body = soapRequest.getSOAPBody();

        XPath xpath = XPathFactory.newInstance().newXPath();
        Node transactionIdNode = (Node) xpath.evaluate(
                "//*[local-name()='requestIds']/*[local-name()='transactionId']",
                body,
                XPathConstants.NODE
        );

        String requestTransactionId = transactionIdNode != null ? transactionIdNode.getTextContent() : "123456789"; // fallback
        String generatedTxnId = generateTransactionId();
        String timestamp = ZonedDateTime.now(ZoneId.of("Europe/London"))
                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX"));

        // Set values in error response
        setNodeValue(doc, "//*[local-name()='refRequestIds']/*[local-name()='transactionId']", requestTransactionId);
        setNodeValue(doc, "//*[local-name()='responseId']/*[local-name()='transactionId']", generatedTxnId);
        setNodeValue(doc, "//*[local-name()='cmdNotifications']/*[local-name()='timestamp']", timestamp);

        // Write modified XML back to response
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        TransformerFactory tf = TransformerFactory.newInstance();
        tf.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        tf.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
        Transformer transformer = tf.newTransformer();
        transformer.transform(new DOMSource(doc), new StreamResult(out));

        WebServiceMessage response = messageContext.getResponse();
        ((SaajSoapMessage) response).getSaajMessage().getSOAPPart()
                .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

    } catch (Exception e) {
        logger.error("Failed to handle schema validation error: {}", e.getMessage(), e);
        return true;
    }

    return false; // prevent further processing
}

/**
 * Helper method to set value using XPath
 */
private void setNodeValue(Document doc, String expression, String value) throws XPathExpressionException {
    XPath xpath = XPathFactory.newInstance().newXPath();
    Node node = (Node) xpath.evaluate(expression, doc, XPathConstants.NODE);
    if (node != null) {
        node.setTextContent(value);
    }
}

/**
 * Helper method to generate random transaction ID
 */
private String generateTransactionId() {
    return "1alN" + UUID.randomUUID().toString().replaceAll("-", "").substring(0, 28) + "h";
}
