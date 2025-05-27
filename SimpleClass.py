package com.rbs.bdd.common;

/**
 * Centralized constants used across the service for validation logic,
 * identifiers, XPath expressions, and configuration values.
 */
public final class ServiceConstants {

    private ServiceConstants() {
        // Prevent instantiation
    }

    // IBAN values
    public static final String IBAN_1 = "GB29NWBK60161331926801";
    public static final String IBAN_2 = "GB82WEST12345698765437";
    public static final String IBAN_3 = "GB94BARC10201530093422";
    public static final String IBAN_4 = "GB33BUKB20201555555567";

    // Code values
    public static final String INTL_BANK_ACCOUNT = "InternationalBankAccountNumber";
    public static final String UK_BASIC_BANK_ACCOUNT = "UKBasicBankAccountNumber";

    // XML/XPath constants
    public static final String RESPONSE_XML_PATH = "static-response/response1.xml";

    public static final String XPATH_TRANSACTION_ID = "//*[local-name()='transactionId']";
    public static final String XPATH_ACCOUNT_STATUS = "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']";
    public static final String XPATH_SWITCHING_STATUS = "//*[local-name()='switchingStatus']/*[local-name()='codeValue']";
    public static final String XPATH_MODULUS_STATUS = "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']";
}





package com.rbs.bdd.application.service;

import com.rbs.bdd.application.exception.AccountValidationException;
import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.application.port.out.AccountValidationPort;
import com.rbs.bdd.common.ServiceConstants;
import com.rbs.bdd.domain.enums.AccountStatus;
import com.rbs.bdd.domain.enums.ModulusCheckStatus;
import com.rbs.bdd.domain.enums.SwitchingStatus;
import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.ws.WebServiceMessage;
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
import javax.xml.transform.stream.StreamSource;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.Optional;
import java.util.UUID;

/**
 * Validates the SOAP request schema and applies business logic
 * to return a transformed static SOAP response using DOM and XPath.
 *
 * Implements {@link AccountValidationPort} as part of the hexagonal architecture.
 * Uses account identifier and code type to determine if the account should be considered
 * valid, and if so, transforms a static response template by injecting dynamic fields.
 */
@Service
@RequiredArgsConstructor
public class AccountValidationService implements AccountValidationPort {

    private static final Logger logger = LoggerFactory.getLogger(AccountValidationService.class);

    /**
     * Validates the XSD schema. This is a placeholder as Spring WS performs schema validation via interceptors.
     *
     * @param request the incoming request to be validated
     */
    @Override
    public void validateSchema(ValidateArrangementForPaymentRequest request) {
        logger.info("Schema validation completed (handled by Spring WS interceptor)");
    }

    /**
     * Applies business rules and transforms the static SOAP response using DOM + XPath.
     * If account conditions match, replaces values in the response. Otherwise, throws a SOAP fault.
     *
     * @param request the incoming SOAP request
     * @param message the outgoing response message to populate
     */
    @Override
    public void validateBusinessRules(ValidateArrangementForPaymentRequest request, WebServiceMessage message) {
        try (InputStream xml = getClass().getClassLoader().getResourceAsStream(ServiceConstants.RESPONSE_XML_PATH)) {
            if (xml == null) throw new SchemaValidationException("Static response XML not found");

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            factory.setXIncludeAware(false);
            factory.setExpandEntityReferences(false);

            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(xml);
            XPath xpath = XPathFactory.newInstance().newXPath();

            RequestParams params = extractRequestDetails(request);
            ResponseConfig config = determineMatchingConfig(params)
                    .orElseThrow(() -> new AccountValidationException("Account Validation failed: account not found"));

            updateResponseDocument(doc, xpath, config);

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            ((SaajSoapMessage) message).getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (AccountValidationException e) {
            logger.error("Validation exception: {}", e.getMessage(), e);
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error during response generation: {}", e.getMessage(), e);
            throw new AccountValidationException("Account validation failed", e);
        }
    }

    /**
     * Extracts identifier, code value, and number of digits from the request payload.
     *
     * @param request SOAP request
     * @return parsed request params
     */
    private RequestParams extractRequestDetails(ValidateArrangementForPaymentRequest request) {
        String identifier = request.getArrangementIdentifier().getIdentifier();
        String codeValue = request.getArrangementIdentifier().getContext().getCodeValue();
        int length = identifier != null ? identifier.length() : 0;
        return new RequestParams(identifier, codeValue, length);
    }

    /**
     * Determines the appropriate response based on the incoming request fields.
     *
     * @param p request parameter holder
     * @return optional config to update the response with
     */
    private Optional<ResponseConfig> determineMatchingConfig(RequestParams p) {
        return switch (p) {
            case RequestParams r when isMatch(r, ServiceConstants.IBAN_1) -> Optional.of(
                    new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS));
            case RequestParams r when isMatch(r, ServiceConstants.IBAN_2) -> Optional.of(
                    new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.PASS));
            case RequestParams r when isMatch(r, ServiceConstants.IBAN_3) -> Optional.of(
                    new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS));
            case RequestParams r when isMatch(r, ServiceConstants.IBAN_4) -> Optional.of(
                    new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.FAILED));
            default -> Optional.empty();
        };
    }

    /**
     * Checks if a request matches a given IBAN rule.
     *
     * @param p    the request parameters
     * @param iban the full IBAN to match against
     * @return true if matches either full IBAN or UK version
     */
    private boolean isMatch(RequestParams p, String iban) {
        String ukEquivalent = extractLast14Digits(iban);
        return (p.numberOfDigits() == 22 && ServiceConstants.INTL_BANK_ACCOUNT.equals(p.codeValue()) && iban.equals(p.identifier()))
                || (p.numberOfDigits() == 14 && ServiceConstants.UK_BASIC_BANK_ACCOUNT.equals(p.codeValue()) && ukEquivalent.equals(p.identifier()));
    }

    /**
     * Extracts the last 14 characters from an IBAN string.
     *
     * @param value input string (typically an IBAN)
     * @return last 14 characters or entire input if shorter
     */
    private String extractLast14Digits(String value) {
        return value != null && value.length() >= 14 ? value.substring(value.length() - 14) : value;
    }

    /**
     * Updates response document nodes using XPath with values from business logic.
     *
     * @param doc    the DOM document to modify
     * @param xpath  XPath engine
     * @param config the new values to set
     * @throws XPathExpressionException if XPath fails
     */
    private void updateResponseDocument(Document doc, XPath xpath, ResponseConfig config) throws XPathExpressionException {
        set(xpath, doc, ServiceConstants.XPATH_TRANSACTION_ID, generateTransactionId());
        set(xpath, doc, ServiceConstants.XPATH_ACCOUNT_STATUS, config.status().getValue());
        set(xpath, doc, ServiceConstants.XPATH_SWITCHING_STATUS, config.switching().getValue());
        set(xpath, doc, ServiceConstants.XPATH_MODULUS_STATUS, config.modulus().getValue());
    }

    /**
     * Updates a DOM node's value using XPath.
     *
     * @param xpath XPath engine
     * @param doc   DOM document
     * @param expr  XPath expression
     * @param value value to assign
     * @throws XPathExpressionException if node is not found
     */
    private void set(XPath xpath, Document doc, String expr, String value) throws XPathExpressionException {
        Node node = (Node) xpath.evaluate(expr, doc, XPathConstants.NODE);
        if (node != null) node.setTextContent(value);
    }

    /**
     * Generates a unique transaction ID used in the response.
     *
     * @return UUID-based transaction ID
     */
    private String generateTransactionId() {
        return "3flS" + UUID.randomUUID().toString().replace("-", "") + "h";
    }

    /**
     * Container record for request data used in rule evaluation.
     *
     * @param identifier      full or partial account number
     * @param codeValue       account type (international/UK)
     * @param numberOfDigits  length of identifier
     */
    private record RequestParams(String identifier, String codeValue, int numberOfDigits) {}

    /**
     * Holds the values to be injected into the SOAP response after rule matching.
     *
     * @param status    account status
     * @param switching switching indicator
     * @param modulus   modulus check result
     */
    private record ResponseConfig(AccountStatus status, SwitchingStatus switching, ModulusCheckStatus modulus) {}
}


/**
 * Creates a secure, namespace-aware {@link DocumentBuilderFactory} instance configured
 * to protect against XML External Entity (XXE) attacks and unsafe XML parsing behavior.
 *
 * @return a secure {@link DocumentBuilderFactory}
 * @throws Exception if factory features cannot be set
 */
private DocumentBuilderFactory createSecureDocumentBuilderFactory() throws Exception {
    DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
    factory.setNamespaceAware(true);
    factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
    factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
    factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
    factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
    factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
    factory.setXIncludeAware(false);
    factory.setExpandEntityReferences(false);
    return factory;
}
