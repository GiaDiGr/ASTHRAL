"""Public bounded failure taxonomy. Never serialize exceptions, prompts or credentials."""
import httpx

SECURITY = frozenset(('STRUCTURED_FACT_REALIZATION_REJECTED','CLINICAL_CLAIM_REQUIRES_EXACT_ENGINE_TEXT','OPTIONAL_DATA_REQUIRES_ENGINE_SUMMARY','CLINICAL_STATE_CONTRADICTION','UNSAFE_GENERATED_TEXT','UNSUPPORTED_NUMBER','UNSUPPORTED_CLINICAL_INTERPRETATION','INVALID_CITATION','UNGROUNDED_MODEL_OUTPUT'))
SCHEMA = frozenset(('INVALID_GENERATED_SCHEMA','INVALID_SENTENCE','INVALID_MODEL_OUTPUT','MODEL_RESPONSE_TOO_LARGE','TRUNCATED_MODEL_RESPONSE'))
def failure_trace(exc):
    code = str(exc)
    if isinstance(exc,httpx.TimeoutException): category,code='TIMEOUT','LOCAL_INFERENCE_TIMEOUT'
    elif isinstance(exc,httpx.HTTPStatusError): category,code='HTTP_STATUS','LOCAL_INFERENCE_HTTP_ERROR'
    elif isinstance(exc,httpx.HTTPError): category,code='TRANSPORT','LOCAL_INFERENCE_TRANSPORT_ERROR'
    elif code in SECURITY: category='SAFETY_REJECTION'
    elif code in SCHEMA: category='MODEL_OUTPUT'
    elif code=='SEMANTIC_GROUNDING_REJECTED': category='VERIFIER_REJECTION'
    elif code=='LLM_BUSY': category='SATURATION'
    elif code=='LLM_DISABLED_OR_MEMORY_PRESSURE': category='RESOURCE_ADMISSION'
    elif isinstance(exc,MemoryError): category,code='RESOURCE_ADMISSION','MEMORY_ERROR'
    else: category,code='UNCLASSIFIED','UNCLASSIFIED_INFERENCE_FAILURE'
    return {'category':category,'code':code,'stage':getattr(exc,'vigile_stage','UNOBSERVED'),
            'exception_type':type(exc).__name__,'clinical_state_changed':False}
