import urllib3
import requests
import json
import click
import os
from os import path

urllib3.disable_warnings()


def get_larkmanager(user_access_token,folder_token):
    from LarkManager import LarkManager
    LarkManager = LarkManager(user_access_token, folder_token)
    return LarkManager


def num_char(total_cols):
    if total_cols <= 26:  # A~Z
        return chr(65 + total_cols - 1)
    elif total_cols % 26 == 0:
        first_char = chr(65 + total_cols // 26 - 2)
        second_char = "Z"
    elif total_cols > 26 * 27:
        print("Too Large For columns")
        return None
    else:  # AA,AB...
        first_char = chr(65 + total_cols // 26 - 1)
        second_char = chr(65 + total_cols % 26 - 1)
    return first_char + second_char
