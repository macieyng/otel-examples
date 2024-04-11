import logging 
from logging.config import dictConfig

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
import opentelemetry
# Yep, I know it's "private", but it's the only way to get it working
# It's "private" just because it's "not stable" 
# yet I'm using this in production since January 2023 with no issues producing ~20GB of logs per day
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.resources import (
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    Resource,
)
import os

from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
import opentelemetry.version

# This is important if you want logs to be easily searchable in Azure Portal Transaction Search
# Feel free to skip it, if you don't care about meta data and just want to log stuff
resource = Resource.create(
    {
        SERVICE_NAME: os.getenv("WEBSITE_SITE_NAME", "unknown-service"),
        SERVICE_INSTANCE_ID: os.getenv("WEBSITE_INSTANCE_ID", "unknown-instance"),
    }
)

logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

# Notes:
# 1. Offline storage will create a local file to store logs in case of network issues
# and retry sending them later. Up to you if you want to disable it. 
# 2. Make sure you have APPLICATIONINSIGHTS_CONNECTION_STRING or APPINSIGHTS_INSTRUMENTATIONKEY 
# set in your environment variables

log_exporter = AzureMonitorLogExporter(disable_offline_storage=True)

logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))


def filter_logs_below_or_equal_to_level(level):
    """
    https://docs.python.org/3/howto/logging-cookbook.html#custom-handling-of-levels
    """
    level = getattr(logging, level)

    def filter(record):
        return record.levelno <= level

    return filter


log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "class": "logging.Formatter",
            # FYI: your custom logs formatting will be ignored by Application Insights anyway... 
            # Don't bother unless you care about stdout/stderr logs
            "format": "%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(module)s.%(funcName)s -: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "warnings_and_below": {
            "()": f"{__name__}.filter_logs_below_or_equal_to_level",
            "level": "WARNING",
        }
    },
    "handlers": {
        # Separate these two to avoid mixing stdout and stderr logs
        # Python will not use stdout with StreamHandler, but stderr will be used
        # stdout logging level < ERROR, stderr logging level >= ERROR
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "filters": ["warnings_and_below"],
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
            "level": "ERROR",
        },
        # Real magic happens here
        "otel": {
            "class": "opentelemetry.sdk._logs.LoggingHandler",
            "logger_provider": logger_provider,
            # No need to add formatter here, it will be ignored by Application Insights
        },
    },
    "loggers": {
        "": {
            "handlers": ["stderr", "stdout"], # this means that all logs will be sent to stdout and/or stderr with respect to their level
            "level": os.getenv("LOGGER_LEVEL", "INFO"),
        },
        # It's a good practice to separate your appliaction logs from packages logs, etc
        # I recommend creating namespace "app" and putting all your logs under this namespace 
        # ie. "app.service.a", "app.routers.b", "app.calculators"
        "app": {
            "handlers": ["otel"], # this means that all logs from "app" namespace will use otel handler
            "level": "INFO",  # only logs with level INFO and above will be bubbled up and catch by otel, stdout and stderr handlers
            # "propagate": False,  # enable this if you don't want logs from "app" namespace to be bubbled up to stdout and stderr handlers
        },
        # my recommendations for azure SDKs, INFO is too verbose
        "azure.core.pipeline.policies.http_logging_policy": {
            "level": "WARNING",  # only logs with level WARNING and above will be bubbled up and catch by stdout and stderr handlers
        },
        # Avoid self reporting
        "azure.monitor.opentelemetry.exporter.export": {
            "level": "WARNING", # only logs with level WARNING and above will be bubbled up and catch by stdout and stderr handlers
        },
        "opentelemetry.attributes": {
            "level": "ERROR", # only logs with level ERROR and above will be bubbled up and catch by stdout and stderr handlers
        },
    },
}


dictConfig(log_config)

logging.info("ℹ️ Root handler, level info is sent only to stdout")
logging.warning("⚠️ Root handler, level warning is sent only to stdout")
logging.error("🚨 Root handler, level error is sent only to stdout and stderr")

logger = logging.getLogger("app")

logger.info("ℹ️ App handler, level info is sent to stdout and Application Insights")
logger.warning("⚠️ App handler, level warning is sent to stdout and Application Insights")
logger.error("🚨 App handler, level error is sent to stdout and stderr and Application Insights")

# Really cool feature is log attribtues that you can add to your logs
# They will be visible in Application Insights under the "Custom Dimensions" tab
# Just remember that these should be namespaces
logger.info(
    "ℹ️ App handler, level info is sent to stdout and Application Insights", 
    extra={
        "otel.version": opentelemetry.version.__version__, 
        "user.id": "JP10-0213-7420-0001",
        "this.module.name.is": __name__ 
    }
)
