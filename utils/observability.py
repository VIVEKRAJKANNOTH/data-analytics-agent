"""
Observability module for logging, tracing, and metrics
"""
import logging
import time
import functools
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import json

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Global instances
tracer_provider: Optional[TracerProvider] = None
meter_provider: Optional[MeterProvider] = None
tracer: Optional[trace.Tracer] = None
meter: Optional[metrics.Meter] = None

# Metrics
request_counter: Optional[metrics.Counter] = None
request_duration: Optional[metrics.Histogram] = None
error_counter: Optional[metrics.Counter] = None
code_execution_counter: Optional[metrics.Counter] = None
code_execution_duration: Optional[metrics.Histogram] = None
llm_request_counter: Optional[metrics.Counter] = None
llm_token_counter: Optional[metrics.Counter] = None


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "backend.log",
    json_format: bool = True
) -> logging.Logger:
    """
    Setup structured logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        json_format: Use JSON formatting for logs
    
    Returns:
        Configured root logger
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Set formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info("Logging initialized", extra={
        "extra_fields": {
            "log_level": log_level,
            "log_file": log_file,
            "json_format": json_format
        }
    })
    
    return logger


def setup_tracing(service_name: str = "data-analytics-agent") -> trace.Tracer:
    """
    Setup OpenTelemetry tracing
    
    Args:
        service_name: Name of the service for tracing
    
    Returns:
        Configured tracer
    """
    global tracer_provider, tracer
    
    # Create resource with service name
    resource = Resource.create({"service.name": service_name})
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Add console exporter for development
    console_exporter = ConsoleSpanExporter()
    span_processor = BatchSpanProcessor(console_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    logging.info("Tracing initialized", extra={
        "extra_fields": {"service_name": service_name}
    })
    
    return tracer


def setup_metrics(service_name: str = "data-analytics-agent") -> metrics.Meter:
    """
    Setup OpenTelemetry metrics
    
    Args:
        service_name: Name of the service for metrics
    
    Returns:
        Configured meter
    """
    global meter_provider, meter
    global request_counter, request_duration, error_counter
    global code_execution_counter, code_execution_duration
    global llm_request_counter, llm_token_counter
    
    # Create resource
    resource = Resource.create({"service.name": service_name})
    
    # Create metric reader with console exporter
    console_exporter = ConsoleMetricExporter()
    metric_reader = PeriodicExportingMetricReader(
        console_exporter,
        export_interval_millis=60000  # Export every 60 seconds
    )
    
    # Create meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    
    # Set as global meter provider
    metrics.set_meter_provider(meter_provider)
    
    # Get meter
    meter = metrics.get_meter(__name__)
    
    # Create common metrics
    request_counter = meter.create_counter(
        name="api_requests_total",
        description="Total number of API requests",
        unit="1"
    )
    
    request_duration = meter.create_histogram(
        name="api_request_duration_seconds",
        description="API request duration in seconds",
        unit="s"
    )
    
    error_counter = meter.create_counter(
        name="errors_total",
        description="Total number of errors",
        unit="1"
    )
    
    code_execution_counter = meter.create_counter(
        name="code_executions_total",
        description="Total number of code executions",
        unit="1"
    )
    
    code_execution_duration = meter.create_histogram(
        name="code_execution_duration_seconds",
        description="Code execution duration in seconds",
        unit="s"
    )
    
    llm_request_counter = meter.create_counter(
        name="llm_requests_total",
        description="Total number of LLM requests",
        unit="1"
    )
    
    llm_token_counter = meter.create_counter(
        name="llm_tokens_total",
        description="Total number of LLM tokens used",
        unit="1"
    )
    
    logging.info("Metrics initialized", extra={
        "extra_fields": {"service_name": service_name}
    })
    
    return meter


def initialize_observability(
    service_name: str = "data-analytics-agent",
    log_level: str = "INFO",
    log_file: str = "backend.log"
) -> Dict[str, Any]:
    """
    Initialize all observability components
    
    Args:
        service_name: Name of the service
        log_level: Logging level
        log_file: Path to log file
    
    Returns:
        Dictionary with logger, tracer, and meter
    """
    logger = setup_logging(log_level=log_level, log_file=log_file)
    tracer = setup_tracing(service_name=service_name)
    meter = setup_metrics(service_name=service_name)
    
    logging.info("Observability initialized successfully", extra={
        "extra_fields": {
            "service_name": service_name,
            "log_level": log_level
        }
    })
    
    return {
        "logger": logger,
        "tracer": tracer,
        "meter": meter
    }


def trace_function(operation_name: Optional[str] = None):
    """
    Decorator to automatically trace function execution
    
    Args:
        operation_name: Optional custom operation name for the span
    
    Example:
        @trace_function("process_data")
        def process_data(data):
            return data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if tracer is None:
                return func(*args, **kwargs)
            
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    span.set_attribute("status", "success")
                    return result
                    
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def measure_time(metric_name: Optional[str] = None, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to measure function execution time
    
    Args:
        metric_name: Optional custom metric name
        labels: Optional labels for the metric
    
    Example:
        @measure_time("data_processing_duration", {"type": "csv"})
        def process_csv(file_path):
            return data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log execution time
                logging.debug(f"{func.__name__} completed", extra={
                    "extra_fields": {
                        "function": func.__name__,
                        "duration_seconds": duration,
                        "status": "success"
                    }
                })
                
                # Record metric if available
                if request_duration is not None:
                    metric_labels = labels or {}
                    metric_labels["function"] = func.__name__
                    request_duration.record(duration, metric_labels)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log error
                logging.error(f"{func.__name__} failed", extra={
                    "extra_fields": {
                        "function": func.__name__,
                        "duration_seconds": duration,
                        "status": "error",
                        "error": str(e)
                    }
                })
                
                # Record error metric
                if error_counter is not None:
                    error_labels = labels or {}
                    error_labels["function"] = func.__name__
                    error_labels["error_type"] = type(e).__name__
                    error_counter.add(1, error_labels)
                
                raise
        
        return wrapper
    return decorator


def get_tracer() -> Optional[trace.Tracer]:
    """Get the global tracer instance"""
    return tracer


def get_meter() -> Optional[metrics.Meter]:
    """Get the global meter instance"""
    return meter


def record_metric(
    metric_type: str,
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """
    Record a custom metric
    
    Args:
        metric_type: Type of metric (counter, histogram, gauge)
        name: Metric name
        value: Metric value
        labels: Optional labels
    """
    if meter is None:
        return
    
    labels = labels or {}
    
    if metric_type == "counter":
        if name == "api_requests_total" and request_counter:
            request_counter.add(value, labels)
        elif name == "errors_total" and error_counter:
            error_counter.add(value, labels)
        elif name == "code_executions_total" and code_execution_counter:
            code_execution_counter.add(value, labels)
        elif name == "llm_requests_total" and llm_request_counter:
            llm_request_counter.add(value, labels)
        elif name == "llm_tokens_total" and llm_token_counter:
            llm_token_counter.add(value, labels)
    
    elif metric_type == "histogram":
        if name == "api_request_duration_seconds" and request_duration:
            request_duration.record(value, labels)
        elif name == "code_execution_duration_seconds" and code_execution_duration:
            code_execution_duration.record(value, labels)
