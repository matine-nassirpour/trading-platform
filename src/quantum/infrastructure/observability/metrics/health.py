from prometheus_client import Gauge

pipeline_up = Gauge("quantum_pipeline_up", "0/1 end-to-end health")
otel_tracing_up = Gauge("quantum_tracing_up", "0/1 tracer init & export ok")
logging_sink_up = Gauge("quantum_logging_sink_up", "0/1 partitioned/audit writable")
