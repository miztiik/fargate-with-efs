# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import random
import time
import fcntl


class GlobalArgs:
    """ Global statics """
    OWNER = "Mystique"
    ENVIRONMENT = "production"
    MODULE_NAME = "greeter_lambda"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    RANDOM_SLEEP_ENABLED = os.getenv("RANDOM_SLEEP_ENABLED", False)
    RANDOM_SLEEP_SECS = int(os.getenv("RANDOM_SLEEP_SECS", 2))
    ANDON_CORD_PULLED = os.getenv("ANDON_CORD_PULLED", False)
    EFS_MNT_PATH = os.getenv("EFS_MNT_PATH", None)


def set_logging(lv=GlobalArgs.LOG_LEVEL):
    """ Helper to enable logging """
    logging.basicConfig(level=lv)
    logger = logging.getLogger()
    logger.setLevel(lv)
    return logger


# Initial some defaults in global context to reduce lambda start time, when re-using container
logger = set_logging()


def random_sleep(max_seconds=10):
    if bool(random.getrandbits(1)):
        logger.info(f"sleep_start_time:{str(datetime.datetime.now())}")
        time.sleep(random.randint(0, max_seconds))
        logger.info(f"sleep_end_time:{str(datetime.datetime.now())}")


def get_messages():
    try:
        MSG_FILE_PATH = f"{GlobalArgs.EFS_MNT_PATH}/index.html"
        with open(MSG_FILE_PATH, "r") as msg_file:
            fcntl.flock(msg_file, fcntl.LOCK_SH)
            msg = msg_file.read()
            fcntl.flock(msg_file, fcntl.LOCK_UN)
            logger.info(f"msg:\n{msg}")
    except:
        msg = "No message yet."
    return msg


def add_message(_msg):
    if _msg:
        MSG_FILE_PATH = f"{GlobalArgs.EFS_MNT_PATH}/index.html"
        # html_content_01 = "<html><head><title>Mystique Automation</title></head><body><h1>"
        html_content_01 = "<html><head><title>Mystique Automation - Modern Web App</title><style>body{margin-top:40px;background-color:#333}</style></head><body><div style=color:white;text-align:center><h1>Modern Web App</h1><h2>Congratulations!</h2>"
        html_content_02 = f"<p>{_msg}</p>"
        # html_content_03 = "</h1></body></html>"
        html_content_03 = "</div></body></html>"
        html_content = html_content_01 + html_content_02 + html_content_03

        # with open(MSG_FILE_PATH, "a") as msg_file:
        with open(MSG_FILE_PATH, "w") as msg_file:
            fcntl.flock(msg_file, fcntl.LOCK_EX)
            msg_file.write(html_content)
            fcntl.flock(msg_file, fcntl.LOCK_UN)


def lambda_handler(event, context):
    logger.info(f"rcvd_evnt:\n{event}")
    greet_msg = "API Method unsupported."

    # random_sleep(GlobalArgs.RANDOM_SLEEP_SECS)
    method = event["requestContext"]["httpMethod"]
    if method == "POST":
        new_message = event.get("body")
        if new_message:
            add_message(new_message)
            get_messages()
            greet_msg = "Message added successfully! Go Rock the world"

    msg = {
        "statusCode": 200,
        "body": (
            f'{{"message": "{greet_msg}",'
            f'"lambda_version":"{context.function_version}",'
            f'"ts": "{str(datetime.datetime.now())}"'
            f'}}'
        )
    }

    return msg
