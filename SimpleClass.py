package com.rbs.bdd.application.service;

import com.rbs.bdd.application.exception.AccountValidationException;
import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.application.port.out.AccountValidationPort;
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
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Service responsible for validating the schema and dynamically modifying a static SOAP response
 * based on identifier and account type logic (IBAN/UK account).
 *
 * Implements {@link AccountValidationPort} for use in hexagonal architecture.
 * Uses DOM parsing and XPath to update SOAP fields like transaction ID, account status,
 * switching status, and modulus check result based on business rules.
 */
@Service
@RequiredArgsConstructor
public class AccountValidationService implements AccountValidationPort {

    private static final Logger logger = LoggerFactory.getLogger(AccountValidationService.class);

    private static final String INTL_BANK_ACCOUNT = "InternationalBankAccountNumber";
    private static final String UK_BASIC_BANK_ACCOUNT = "UKBasicBankAccountNumber";

    private static final List<AccountRule> RULES = List.of(
            new AccountRule("GB29NWBK60161331926801", AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS),
            new AccountRule("GB82WEST12345698765437", AccountStatus.DOMESTIC_RESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.PASS),
            new AccountRule("GB94BARC10201530093422", AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.SWITCHED, ModulusCheckStatus.PASS),
            new AccountRule("GB33BUKB20201555555567", AccountStatus.DOMESTIC_UNRESTRICTED, SwitchingStatus.NOT_SWITCHING, ModulusCheckStatus.FAILED)
    );

    /**
     * Schema validation (currently delegated to Spring WS interceptor).
     *
     * @param request the SOAP payload
     */
    @Override
    public void validateSchema(ValidateArrangementForPaymentRequest request) {
        logger.info("Schema validation completed (handled by Spring WS interceptor)");
    }

    /**
     * Loads the static XML response, matches business rules, applies modifications,
     * and writes the final response to the WebServiceMessage.
     *
     * @param request SOAP request data
     * @param message WebServiceMessage response to be populated
     */
    @Override
    public void validateBusinessRules(ValidateArrangementForPaymentRequest request, WebServiceMessage message) {
        try (InputStream xml = getClass().getClassLoader().getResourceAsStream("static-response/response1.xml")) {
            if (xml == null) throw new SchemaValidationException("response1.xml not found");

            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            factory.setXIncludeAware(false);
            factory.setExpandEntityReferences(false);

            Document doc = factory.newDocumentBuilder().parse(xml);
            XPath xpath = XPathFactory.newInstance().newXPath();

            RequestParams params = extractRequestDetails(request);
            ResponseConfig config = determineResponseConfig(params)
                    .orElseThrow(() -> new AccountValidationException("Account Validation failed: account not found"));

            applyResponse(doc, xpath, config);

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            TransformerFactory transformerFactory = TransformerFactory.newInstance();
            transformerFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            transformerFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
            Transformer transformer = transformerFactory.newTransformer();
            transformer.transform(new DOMSource(doc), new StreamResult(out));

            ((SaajSoapMessage) message).getSaajMessage().getSOAPPart()
                    .setContent(new StreamSource(new ByteArrayInputStream(out.toByteArray())));

        } catch (AccountValidationException e) {
            logger.error("Business rule not matched: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Business rule processing failed: {}", e.getMessage(), e);
            throw new AccountValidationException("Account Validation Failed", e);
        }
    }

    /**
     * Extracts IBAN/account identifier and account type code from the request.
     */
    private RequestParams extractRequestDetails(ValidateArrangementForPaymentRequest request) {
        String id = request.getArrangementIdentifier().getIdentifier();
        String code = request.getArrangementIdentifier().getContext().getCodeValue();
        return new RequestParams(id, code, id != null ? id.length() : 0);
    }

    /**
     * Iterates over preconfigured rules and checks for a match.
     */
    private Optional<ResponseConfig> determineResponseConfig(RequestParams params) {
        return RULES.stream()
                .filter(rule -> matchAccountRule(rule, params))
                .findFirst()
                .map(rule -> new ResponseConfig(rule.status(), rule.switching(), rule.modulus()));
    }

    /**
     * Matches a single rule against the request parameters using account type and ID.
     *
     * @param rule   the account rule
     * @param params the request parameters
     * @return true if the rule matches
     */
    private boolean matchAccountRule(AccountRule rule, RequestParams params) {
        if (params.codeValue().equals(INTL_BANK_ACCOUNT) &&
                params.numberOfDigits() == 22 &&
                params.identifier().equals(rule.iban())) {
            return true;
        }

        if (params.codeValue().equals(UK_BASIC_BANK_ACCOUNT) &&
                params.numberOfDigits() == 14 &&
                params.identifier().equals(extractLast14Digits(rule.iban()))) {
            return true;
        }

        return false;
    }

    /**
     * Applies updated values to static SOAP response using XPath.
     */
    private void applyResponse(Document doc, XPath xpath, ResponseConfig config) throws XPathExpressionException {
        set(xpath, doc, "//*[local-name()='transactionId']", generateTransactionId());
        set(xpath, doc, "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']", config.status().getValue());
        set(xpath, doc, "//*[local-name()='switchingStatus']/*[local-name()='codeValue']", config.switching().getValue());
        set(xpath, doc, "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']", config.modulus().getValue());
    }

    /**
     * Utility method to set a value using XPath in the DOM tree.
     */
    private void set(XPath xpath, Document doc, String expr, String value






                     ----/


                     
