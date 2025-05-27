/**
 * Service class responsible for handling schema validation and dynamic response transformation
 * for the validateArrangementForPayment SOAP operation.
 *
 * <p>This class uses DOM + XPath to read a static SOAP response template and apply specific
 * business rules based on the incoming request's identifier and code value.</p>
 *
 * <p>The matching scenarios include combinations of IBAN and UK bank account numbers,
 * with outcomes that set account status, switching status, and modulus check results.</p>
 *
 * <p>If no matching rule is found, a custom {@link AccountValidationException} is thrown,
 * returning a SOAP fault to the client.</p>
 *
 * Implements the {@link AccountValidationPort} interface as part of the hexagonal architecture.
 */
@Service
@RequiredArgsConstructor
public class AccountValidationService implements AccountValidationPort {

    private static final Logger logger = LoggerFactory.getLogger(AccountValidationService.class);

    /**
     * Validates the SOAP request schema using Spring WS interceptor.
     * No additional logic is implemented here.
     *
     * @param request the SOAP request object
     */
    @Override
    public void validateSchema(ValidateArrangementForPaymentRequest request) {
        logger.info("Schema validation completed (handled by Spring WS interceptor)");
    }

    /**
     * Applies business logic to a static SOAP response XML based on request identifier and code value.
     * Modifies fields like transactionId, account status, switching status, and modulus check result.
     * Writes the final response to the outgoing {@link WebServiceMessage}.
     *
     * @param request the incoming SOAP request payload
     * @param message the outgoing SOAP message to be modified
     * @throws AccountValidationException if no matching rule is found or processing fails
     */
    @Override
    public void validateBusinessRules(ValidateArrangementForPaymentRequest request, WebServiceMessage message) {
        try {
            InputStream xml = getClass().getClassLoader().getResourceAsStream("static-response/response1.xml");
            if (xml == null) throw new SchemaValidationException("response1.xml not found");

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);
            XPath xpath = XPathFactory.newInstance().newXPath();

            RequestParams params = extractRequestDetails(request);
            ResponseConfig config = determineResponseConfig(params)
                    .orElseThrow(() -> new AccountValidationException("Account Validation failed: account not found"));

            applyResponse(doc, xpath, config);

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            ((SaajSoapMessage) message).getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (AccountValidationException e) {
            logger.error("Error in AccountValidationException: {}", e.getMessage(), e);
            throw new AccountValidationException("Account Validation failed: account not found", e);
        } catch (Exception e) {
            logger.error("Error in validateBusinessRules: {}", e.getMessage(), e);
            throw new AccountValidationException("Business rule processing failed", e);
        }
    }

    /**
     * Extracts key request values needed for business rule evaluation.
     *
     * @param request the incoming SOAP request
     * @return a structured {@link RequestParams} record containing identifier, code, and length
     */
    private RequestParams extractRequestDetails(ValidateArrangementForPaymentRequest request) {
        String identifier = request.getArrangementIdentifier().getIdentifier();
        String codeValue = request.getArrangementIdentifier().getContext().getCodeValue();
        int length = identifier != null ? identifier.length() : 0;
        return new RequestParams(identifier, codeValue, length);
    }

    /**
     * Evaluates the incoming request and determines the appropriate business rule to apply.
     *
     * @param p the extracted {@link RequestParams}
     * @return an {@link Optional} containing {@link ResponseConfig} if a match is found
     */
    private Optional<ResponseConfig> determineResponseConfig(RequestParams p) {
        String id = p.identifier();
        int len = p.numberOfDigits();
        String code = p.codeValue();

        String ibanAccount1 = "GB29NWBK60161331926801";
        String ibanAccount2 = "GB82WEST12345698765437";
        String ibanAccount3 = "GB94BARC10201530093422";
        String ibanAccount4 = "GB33BUKB20201555555567";

        String account1 = extractLast14Digits(ibanAccount1);
        String account2 = extractLast14Digits(ibanAccount2);
        String account3 = extractLast14Digits(ibanAccount3);
        String account4 = extractLast14Digits(ibanAccount4);

        logger.info("Account 1: {}", account1);
        logger.info("Account 2: {}", account2);
        logger.info("Account 3: {}", account3);
        logger.info("Account 4: {}", account4);

        if ((len == 22 && code.equals("InternationalBankAccountNumber") && id.equals(ibanAccount1))
                || (len == 14 && code.equals("UKBasicBankAccountNumber") && id.equals(account1))) {
            logger.info("Account is Domestic-Restricted, Switched, and modulus is passed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS));
        } else if ((len == 22 && code.equals("InternationalBankAccountNumber") && id.equals(ibanAccount2))
                || (len == 14 && code.equals("UKBasicBankAccountNumber") && id.equals(account2))) {
            logger.info("Account is Domestic-Restricted, NotSwitching, and modulus is passed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.PASS));
        } else if ((len == 22 && code.equals("InternationalBankAccountNumber") && id.equals(ibanAccount3))
                || (len == 14 && code.equals("UKBasicBankAccountNumber") && id.equals(account3))) {
            logger.info("Account is Domestic-Unrestricted, Switched, and modulus is passed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS));
        } else if ((len == 22 && code.equals("InternationalBankAccountNumber") && id.equals(ibanAccount4))
                || (len == 14 && code.equals("UKBasicBankAccountNumber") && id.equals(account4))) {
            logger.info("Account is Domestic-Unrestricted, NotSwitching, and modulus is failed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.FAILED));
        }

        return Optional.empty();
    }

    /**
     * Extracts the last 14 digits of a given IBAN account string.
     *
     * @param iban the full IBAN string
     * @return the last 14 characters, or the full input if less than 14
     */
    private String extractLast14Digits(String iban) {
        return iban != null && iban.length() >= 14 ? iban.substring(iban.length() - 14) : iban;
    }

    /**
     * Updates specific fields in the static response XML using the resolved response configuration.
     *
     * @param doc    the parsed DOM XML document
     * @param xpath  the XPath evaluator
     * @param config the response configuration to apply
     * @throws XPathExpressionException if any XPath update fails
     */
    private void applyResponse(Document doc, XPath xpath, ResponseConfig config) throws XPathExpressionException {
        String transactionId = generateTransactionId();
        logger.info("Transaction ID: {}", transactionId);
        logger.info("Account Type: {}", config.status().getValue());
        logger.info("Switching: {}", config.switching().getValue());
        logger.info("Modulus: {}", config.modulus().getValue());

        set(xpath, doc, "//*[local-name()='transactionId']", transactionId);
        set(xpath, doc, "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']", config.status().getValue());
        set(xpath, doc, "//*[local-name()='switchingStatus']/*[local-name()='codeValue']", config.switching().getValue());
        set(xpath, doc, "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']", config.modulus().getValue());
    }

    /**
     * Utility method to update a node in the XML document using XPath.
     *
     * @param xpath XPath evaluator
     * @param doc   DOM document
     * @param expr  XPath expression to locate the node
     * @param value the value to set on the node
     * @throws XPathExpressionException if the expression fails
     */
    private void set(XPath xpath, Document doc, String expr, String value) throws XPathExpressionException {
        Node node = (Node) xpath.evaluate(expr, doc, XPathConstants.NODE);
        if (node != null) node.setTextContent(value);
    }

    /**
     * Generates a unique transaction ID by appending a UUID to a prefix and suffix.
     *
     * @return a unique transaction string
     */
    private String generateTransactionId() {
        return "3flS" + UUID.randomUUID().toString().replace("-", "") + "h";
    }

    /**
     * Immutable record representing extracted request values.
     *
     * @param identifier      the IBAN or UK account number
     * @param codeValue       the code type (e.g., InternationalBankAccountNumber)
     * @param numberOfDigits  number of characters in the identifier
     */
    private record RequestParams(String identifier, String codeValue, int numberOfDigits) {}

    /**
     * Immutable record representing business rule results to apply in the response.
     *
     * @param status    the account status
     * @param switching the switching status
     * @param modulus   the modulus check result
     */
    private record ResponseConfig(AccountStatus status, SwitchingStatus switching, ModulusCheckStatus modulus) {}
}
