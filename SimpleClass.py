package com.rbs.bdd.application.service;


import com.rbs.bdd.application.exception.AccountValidationException;
import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.application.port.out.AccountValidationPort;
import com.rbs.bdd.domain.enums.AccountStatus;
import com.rbs.bdd.domain.enums.ModulusCheckStatus;
import com.rbs.bdd.domain.enums.SwitchingStatus;
import com.rbs.bdd.generated.*;
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
import java.lang.Exception;
import java.util.UUID;
import java.util.Optional;

/**
 * Service class responsible for handling schema validation and dynamic response transformation
 * for the validateArrangementForPayment SOAP operation.
 *
 * This class uses DOM + XPath to read a static SOAP response template and apply specific
 * business rules based on the incoming request's identifier and code value.</p>
 *
 * The matching scenarios include combinations of IBAN and UK bank account numbers,
 * with outcomes that set account status, switching status, and modulus check results.</p>
 *
 * If no matching rule is found, a custom {@link AccountValidationException} is thrown,
 * returning a SOAP fault to the client.</p>
 *
 * Implements the {@link AccountValidationPort} interface as part of the hexagonal architecture.
 */
@Service
@RequiredArgsConstructor
public class AccountValidationService implements AccountValidationPort {

    private static final Logger logger = LoggerFactory.getLogger(AccountValidationService.class);

    private static final  String ibanAccount1 = "GB29NWBK60161331926801";
    private static final String ibanAccount2 = "GB82WEST12345698765437";
    private static final String ibanAccount3 = "GB94BARC10201530093422";
    private static final String ibanAccount4 = "GB33BUKB20201555555567";
    private static final String INTL_BANK_ACCOUNT="InternationalBankAccountNumber";
    private static final String UK_BASIC_BANK_ACCOUNT="UKBasicBankAccountNumber";
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
            // Block XXE vulnerabilities
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
            ResponseConfig config = determineResponseConfig(params)
                    .orElseThrow(() -> new AccountValidationException("Account Validation failed: account not found"));

            applyResponse(doc, xpath, config);

            ByteArrayOutputStream out = new ByteArrayOutputStream();

            TransformerFactory transformerFactory = TransformerFactory.newInstance();
            transformerFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD,"");
            transformerFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET,"");
            Transformer transformer = transformerFactory.newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            ((SaajSoapMessage) message).getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (AccountValidationException e) {
            logger.error("Error in AccountValidationException: {}", e.getMessage(), e);
            throw e;
        } catch (Exception e) {
            logger.error("Error in validateBusinessRules: {}", e.getMessage(), e);
            throw new AccountValidationException("Account Validation Failed: ", e);
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
        String account1 = extractLast14Digits(ibanAccount1);
        String account2 = extractLast14Digits(ibanAccount2);
        String account3 = extractLast14Digits(ibanAccount3);
        String account4 = extractLast14Digits(ibanAccount4);
        logger.info("Account 1: {}", account1);
        logger.info("Account 2: {}", account2);
        logger.info("Account 3: {}", account3);
        logger.info("Account 4: {}", account4);
        if ((len == 22 && code.equals(INTL_BANK_ACCOUNT) && id.equals(ibanAccount1))
                || (len == 14 && code.equals(UK_BASIC_BANK_ACCOUNT) && id.equals(account1))) {
            logger.info("Account is Domestic-Restricted, Switched, and modulus is passed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS));
        } else if ((len == 22 && code.equals(INTL_BANK_ACCOUNT) && id.equals(ibanAccount2))
                || (len == 14 && code.equals(UK_BASIC_BANK_ACCOUNT) && id.equals(account2))) {
            logger.info("Account is Domestic-Restricted, NotSwitching, and modulus is passed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.PASS));
        } else if ((len == 22 && code.equals(INTL_BANK_ACCOUNT) && id.equals(ibanAccount3))
                || (len == 14 && code.equals(UK_BASIC_BANK_ACCOUNT) && id.equals(account3))) {
            logger.info("Account is Domestic-Unrestricted, Switched, and modulus is passed");
            return Optional.of(new ResponseConfig(AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS));
        } else if ((len == 22 && code.equals(INTL_BANK_ACCOUNT) && id.equals(ibanAccount4))
                || (len == 14 && code.equals(UK_BASIC_BANK_ACCOUNT) && id.equals(account4))) {
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
     * This encapsulates the input fields required to determine which account configuration applies.
     * @param identifier      the IBAN or UK account number
     * @param codeValue       the code type (e.g., InternationalBankAccountNumber)
     * @param numberOfDigits  number of characters in the identifier
     */
    private record RequestParams(String identifier, String codeValue, int numberOfDigits) {
        //This record act as data carrier between schema parsing and business rule engine
    }

    /**
     * Immutable record representing business rule results to apply in the response.
     * This holds the mapped response values after matching input against business rules.
     * @param status    the account status
     * @param switching the switching status
     * @param modulus   the modulus check result
     */
    private record ResponseConfig(AccountStatus status, SwitchingStatus switching, ModulusCheckStatus modulus) {}
    // Acts as a container for response attributes derived from business rules.
}
