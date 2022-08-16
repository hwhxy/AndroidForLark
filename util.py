import urllib3
import json
import os
from os import path
import click
import requests
urllib3.disable_warnings()


def get_larkmanager():
    from AndroidForLark.LarkManager import LarkManager
    user_access_token = "xxxx"
    folder_token = "xxxx"
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
