import logging 
from sys import stdout, stderr

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
import opentelemetry
# yep, I know it's "private", but it's the only way to get it working
# It's "private" just because it's "not stable" 
# yet I'm using this in production since January 2023 with no issues producing ~20GB of logs per day
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler

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

otel_handler = LoggingHandler(logger_provider=logger_provider)
otel_handler.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(stdout)
stdout_handler.setLevel(logging.INFO)

def filter_logs_below_or_equal_to_level(level):
    """
    https://docs.python.org/3/howto/logging-cookbook.html#custom-handling-of-levels
    """
    
    level = getattr(logging, level)

    def filter(record):
        return record.levelno <= level

    return filter


stdout_handler.addFilter(filter_logs_below_or_equal_to_level("WARNING"))

stderr_handler = logging.StreamHandler(stderr)
stderr_handler.setLevel(logging.ERROR)

app_logger = logging.getLogger("app")
app_logger.addHandler(otel_handler)
app_logger.setLevel(logging.INFO)


logging.info("ℹ️ Root handler, level info is sent only to stdout")
logging.warning("⚠️ Root handler, level warning is sent only to stdout")
logging.error("🚨 Root handler, level error is sent only to stdout and stderr")

app_logger.info("ℹ️ App handler, level info is sent to stdout and Application Insights")
app_logger.warning("⚠️ App handler, level warning is sent to stdout and Application Insights")
app_logger.error("🚨 App handler, level error is sent to stdout and stderr and Application Insights")

# Really cool feature is log attribtues that you can add to your logs
# They will be visible in Application Insights under the "Custom Dimensions" tab
# Just remember that these should be namespaces
app_logger.info(
    "ℹ️ App handler, level info is sent to stdout and Application Insights", 
    extra={
        "otel.version": opentelemetry.version.__version__, 
        "user.id": "JP10-0213-7420-0002",
        "this.module.name.is": __name__ 
    }
)
