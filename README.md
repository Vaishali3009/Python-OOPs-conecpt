package com.rbs.bdd.exception;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.ws.soap.SoapMessageCreationException;

import java.io.IOException;

@ControllerAdvice
public class GlobalSoapExceptionHandler {

    @ExceptionHandler(SoapMessageCreationException.class)
    public void handleMalformedXml(Exception ex, HttpServletResponse response) throws IOException {
        response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
        response.setContentType("text/xml");

        String error = """
            <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
              <env:Body>
                <env:Fault>
                  <faultcode>env:Client</faultcode>
                  <faultstring>Internal Error</faultstring>
                </env:Fault>
              </env:Body>
            </env:Envelope>
            """;

        response.getWriter().write(error);
    }
}
