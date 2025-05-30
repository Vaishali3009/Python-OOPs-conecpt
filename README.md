import org.springframework.ws.soap.server.endpoint.SoapFaultMappingExceptionResolver;
import org.springframework.ws.soap.SoapBody;
import org.springframework.ws.soap.SoapFault;
import org.springframework.ws.soap.SoapMessage;

import javax.xml.soap.SOAPException;
import java.util.Properties;

public class CustomSoapFaultResolver extends SoapFaultMappingExceptionResolver {

    public CustomSoapFaultResolver() {
        super.setOrder(1); // Make sure it takes precedence
        Properties errorMappings = new Properties();
        errorMappings.setProperty(Exception.class.getName(), "SERVER");
        setExceptionMappings(errorMappings);
    }

    @Override
    protected void customizeFault(Object endpoint, Exception ex, SoapFault fault) {
        fault.setFaultStringOrReason("Internal Error");
    }
}






@Bean
public SoapFaultMappingExceptionResolver exceptionResolver() {
    return new CustomSoapFaultResolver();
}
