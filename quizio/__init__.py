import logging
import logging.handlers
import sys
import colorlog

from quizio.settings import DEBUG

# set default logging to stdout
# Define a custom formatter with colors
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
    reset=True,
    log_colors={
        "DEBUG": "blue",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

console_handler = logging.StreamHandler()

# Set the formatter to the handler
console_handler.setFormatter(formatter)

logging.getLogger().addHandler(console_handler)
