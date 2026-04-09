from natsrpy.instrumentation import NatsrpyInstrumentor

NatsrpyInstrumentor().instrument(
    # If true, then message payload will be attached
    # to some spans.
    capture_body=False,
    # If true, then message headers will be attached
    # to some spans.
    capture_headers=False,
)

# We also support zero-code instrumentation.
# In case if you're using it, you can specify those parameters
# by setting the following environment variables:
# * `OTEL_PYTHON_NATSRPY_CAPTURE_BODY=true`
# * `OTEL_PYTHON_NATSRPY_CAPTURE_HEADERS=true`
