etc.)

    @Bean
    public SoapFaultMappingExceptionResolver exceptionResolver() {
        SoapFaultMappingExceptionResolver resolver = new SoapFaultMappingExceptionResolver();
        resolver.setOrder(1); // Ensure this has high precedence

        // Map exceptions to SOAP fault codes
        Properties errorMappings = new Properties();
        errorMappings.setProperty(Exception.class.getName(), SoapFaultDefinition.SERVER.toString());
        resolver.setExceptionMappings(errorMappings);

        // Define default SOAP fault
        SoapFaultDefinition defaultFault = new SoapFaultDefinition();
        defaultFault.setFaultCode(SoapFaultDefinition.SERVER);
        defaultFault.setFaultStringOrReason("Internal Error"); // Will appear in <faultstring>
        resolver.setDefaultFault(defaultFault);

        return resolver;
    }
}
