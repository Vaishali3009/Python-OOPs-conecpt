
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
