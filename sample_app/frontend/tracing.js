const { trace } = require('@opentelemetry/api');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { ConsoleSpanExporter } = require('@opentelemetry/tracing');

const provider = new NodeTracerProvider();
const exporter = new ConsoleSpanExporter();

provider.addSpanProcessor(new SimpleSpanProcessor(exporter));

// Example usage
const tracer = trace.getTracer('my-app-frontend');