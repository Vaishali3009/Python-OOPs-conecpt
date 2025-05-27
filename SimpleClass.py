package com.rbs.bdd.application.service;

import com.rbs.bdd.application.exception.AccountValidationException;
import com.rbs.bdd.application.exception.SchemaValidationException;
import com.rbs.bdd.generated.ValidateArrangementForPaymentRequest;
import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBElement;
import jakarta.xml.bind.Unmarshaller;
import jakarta.xml.soap.MessageFactory;
import jakarta.xml.soap.SOAPBody;
import jakarta.xml.soap.SOAPMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.ws.WebServiceMessage;
import org.springframework.ws.soap.saaj.SaajSoapMessage;
import org.w3c.dom.Document;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathFactory;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

class AccountValidationServiceTest {

    private AccountValidationService accountValidationService;

    @BeforeEach
    void setup() {
        accountValidationService = new AccountValidationService();
    }

    private ValidateArrangementForPaymentRequest loadRequest(String identifier, String codeValue) throws Exception {
        String template = Files.readString(Path.of("src/test/resources/static-request/static-request.xml"));
        String finalXml = template
                .replace("${IDENTIFIER}", identifier)
                .replace("${CODEVALUE}", codeValue);

        SOAPMessage soapMessage = MessageFactory.newInstance()
                .createMessage(null, new ByteArrayInputStream(finalXml.getBytes(StandardCharsets.UTF_8)));
        SOAPBody body = soapMessage.getSOAPBody();

        JAXBContext jaxbContext = JAXBContext.newInstance(ValidateArrangementForPaymentRequest.class);
        Unmarshaller unmarshaller = jaxbContext.createUnmarshaller();
        JAXBElement<ValidateArrangementForPaymentRequest> jaxbElement =
                unmarshaller.unmarshal(body.getElementsByTagNameNS("*", "validateArrangementForPayment").item(0),
                        ValidateArrangementForPaymentRequest.class);

        return jaxbElement.getValue();
    }

    private Document invokeServiceAndGetModifiedDoc(ValidateArrangementForPaymentRequest request) throws Exception {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        WebServiceMessage message = new SaajSoapMessage(MessageFactory.newInstance().createMessage());
        accountValidationService.validateSchema(request);
        accountValidationService.validateBusinessRules(request, message);
        message.writeTo(outputStream);

        return DocumentBuilderFactory.newInstance().newDocumentBuilder()
                .parse(new ByteArrayInputStream(outputStream.toByteArray()));
    }

    private String getXpathValue(Document doc, String expression) throws Exception {
        XPath xpath = XPathFactory.newInstance().newXPath();
        return xpath.evaluate(expression, doc);
    }

    @Test
    void testScenario1_Restricted_Switched_Pass() throws Exception {
        //ValidateArrangementForPaymentRequest req = loadRequest("GB29NWBK60161331926801", "InternationalBankAccountNumber");
        ValidateArrangementForPaymentRequest req = loadRequest("60161331926801", "UKBasicBankAccountNumber");

        Document doc = invokeServiceAndGetModifiedDoc(req);
        assertEquals("Domestic - Restricted", getXpathValue(doc, "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']"));
        assertEquals("Switched", getXpathValue(doc, "//*[local-name()='switchingStatus']/*[local-name()='codeValue']"));
        assertEquals("Passed", getXpathValue(doc, "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']"));
    }

    @Test
    void testScenario2_Restricted_NotSwitching_Pass() throws Exception {
      //  ValidateArrangementForPaymentRequest req = loadRequest("GB82WEST12345698765437", "InternationalBankAccountNumber");
        ValidateArrangementForPaymentRequest req = loadRequest("12345698765437", "UKBasicBankAccountNumber");
        Document doc = invokeServiceAndGetModifiedDoc(req);
        assertEquals("Domestic - Restricted", getXpathValue(doc, "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']"));
        assertEquals("Not Switching", getXpathValue(doc, "//*[local-name()='switchingStatus']/*[local-name()='codeValue']"));
        assertEquals("Passed", getXpathValue(doc, "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']"));
    }

    @Test
    void testScenario3_Unrestricted_Switched_Pass() throws Exception {
       // ValidateArrangementForPaymentRequest req = loadRequest("GB94BARC10201530093422", "InternationalBankAccountNumber");
        ValidateArrangementForPaymentRequest req = loadRequest("10201530093422", "UKBasicBankAccountNumber");
        Document doc = invokeServiceAndGetModifiedDoc(req);
        assertEquals("Domestic - Unrestricted", getXpathValue(doc, "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']"));
        assertEquals("Switched", getXpathValue(doc, "//*[local-name()='switchingStatus']/*[local-name()='codeValue']"));
        assertEquals("Passed", getXpathValue(doc, "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']"));
    }

    @Test
    void testScenario4_Unrestricted_NotSwitching_Failed() throws Exception {
        ValidateArrangementForPaymentRequest req = loadRequest("GB33BUKB20201555555567", "InternationalBankAccountNumber");
       // ValidateArrangementForPaymentRequest req = loadRequest("20201555555567", "UKBasicBankAccountNumber");
        Document doc = invokeServiceAndGetModifiedDoc(req);
        assertEquals("Domestic - Unrestricted", getXpathValue(doc, "//*[local-name()='accountingUnits']/*[local-name()='status']/*[local-name()='codeValue']"));
        assertEquals("Not Switching", getXpathValue(doc, "//*[local-name()='switchingStatus']/*[local-name()='codeValue']"));
        assertEquals("Failed", getXpathValue(doc, "//*[local-name()='modulusCheckStatus']/*[local-name()='codeValue']"));
    }

    @Test
    void testNoMatchingScenario_shouldThrowException() throws Exception {
        ValidateArrangementForPaymentRequest req = loadRequest("GB00XXXX00000000000000", "InternationalBankAccountNumber");
        WebServiceMessage message = new SaajSoapMessage(MessageFactory.newInstance().createMessage());

        Exception exception = assertThrows(AccountValidationException.class, () ->
                accountValidationService.validateBusinessRules(req, message));
        assertTrue(exception.getMessage().contains("Account Validation failed: account not found"));
    }
}
