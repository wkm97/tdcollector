from datetime import datetime
import requests
import time
from functools import wraps
import json
from hashlib import sha256
from urllib.parse import urlencode
import re

COOKIE = "visid_incap_3057414=O7vL8YLNT2e/BUAerwjS9jSP+mcAAAAAQUIPAAAAAAAY6GcEAynMNKgBJbAwlbNx; visid_incap_2993746=DKwY0xq7SKG70Hbq+JYPnAWe+mcAAAAAQUIPAAAAAAA3/+h0pd5NJYtzz5QWI9Ov; INIT_PORTAL=7023; wk8XJKsjpt60BnltX9hNtw===nlCRYGb1gUGYjK0gliqA2A%3D%3D%20utVddUw0Kwe6SEJi3KkuCg%3D%3D; staffJobId=621576; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22600381%22%2C%22first_id%22%3A%221962abf69b0155e-0dcd8098d3d2c5-7e433c49-3686400-1962abf69b12517%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk2MmFiZjY5YjAxNTVlLTBkY2Q4MDk4ZDNkMmM1LTdlNDMzYzQ5LTM2ODY0MDAtMTk2MmFiZjY5YjEyNTE3IiwiJGlkZW50aXR5X2xvZ2luX2lkIjoiNjAwMzgxIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22600381%22%7D%2C%22%24device_id%22%3A%221962f61ba232e8-0f7a6a9d2e908a-7e433c49-3686400-1962f61ba2422b6%22%7D; areaId=280; orgId=600381; userId=621576; ZSMART_LOCALE=en; incap_ses_1136_3057414=HX0+LndJQEku7yNlQ+LDDx1CEmgAAAAAqkZ2jH7MGMyOWzA9WIww3Q==; incap_ses_1671_3057414=Gfg2B2071iQbmSAO8JUwF/ICE2gAAAAAU0VKyT2O6fiCTyHcKzmBMw==; SESSION=4edbf1ef-3f16-4df1-b4a7-37597f93d369; HTML_VERSION=1746083070438"

def rate_limit(calls_per_second):
    """
    A simple rate limiting decorator.

    Args:
        calls_per_second (float): The maximum number of calls allowed per second.
    """
    interval = 1.0 / calls_per_second
    last_call = 0.0

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            now = time.time()
            elapsed_time = now - last_call
            if elapsed_time < interval:
                time_to_wait = interval - elapsed_time
                time.sleep(time_to_wait)
                now = time.time()  # Update 'now' after waiting
            last_call = now
            return func(*args, **kwargs)

        return wrapper

    return decorator


def generateSigncode(method: str, path: str, data: dict):
    def hash(content):
        return sha256(content.encode("utf-8")).hexdigest()

    if method.lower() == "get":
        return hash(path + urlencode(data) + "32BytesString")
    else:
        jsonString = json.dumps(data)
        jsonString = re.sub(r"[^a-zA-Z0-9]", "", jsonString)
        jsonString = re.sub(r"null", "", jsonString)
        return hash(path + jsonString + "32BytesString")


@rate_limit(calls_per_second=1)
def get_order_list(data):
    path = "/cee/order/v2/getCeeOrderList"
    signcode = generateSigncode("post", path, data)
    # data = {
    #     "dPartyCode": 621564,
    #     "pageSize": 10,
    #     "onWayFlag": "Y",
    #     "pageNum": 1,
    #     "dPartyType": "E",
    #     "extData": {"senario": "esales-monthly-order"},
    # }
    response = requests.post(
        f"https://dealer.unifi.com.my/portal/esales/api{path}",
        headers={
            "Cookie": COOKIE,
            "signcode": signcode,
        },
        json=data,
    )
    return response


def get_all_order_list(staffId, onWayFlag, createdDateFrom = None, createdDateTo = None):
    # staffId: 621394
    # onWayFlag: Y
    # createdDateFrom: 20250401000000
    # createdDateTo: 20250430235959
    page_number = 1
    results = []

    while True:
        if onWayFlag == "Y":
            data = {
                "dPartyCode": staffId,
                "pageSize": 50,
                "onWayFlag": onWayFlag,  # Y/N
                "pageNum": page_number,
                "dPartyType": "E",
                "extData": {"senario": "esales-monthly-order"},
            }
        else:
            data = {
                "dPartyCode": staffId,
                "pageSize": 50,
                "onWayFlag": onWayFlag,  # Y/N
                "pageNum": page_number,
                "dPartyType": "E",
                "extData": {"senario": "esales-monthly-order"},
                "createdDateFrom": createdDateFrom,
                "createdDateTo": createdDateTo,
            }
        response = get_order_list(data)
        result_json = response.json()
        results = [*results, *result_json["data"]]
        if len(result_json["data"]) != data["pageSize"]:
            break
        else:
            page_number += 1
    return results


@rate_limit(calls_per_second=1)
def get_order_detail(data):
    path = "/cee/order/v2/getCeeOrderDetail"
    signcode = generateSigncode("post", path, data)
    # data = {"custOrderId": "2502000060013514", "custOrderNbr": "2502000060013514"}
    response = requests.post(
        f"https://dealer.unifi.com.my/portal/esales/api{path}",
        headers={
            "Cookie": COOKIE,
            "signcode": signcode,
        },
        json=data,
    )
    return response


@rate_limit(calls_per_second=1)
def get_staff_detail(data):
    path = "/saleschannel/getStaffDetail"
    signcode = generateSigncode("post", path, data)
    response = requests.post(
        f"https://dealer.unifi.com.my/portal/esales/api{path}",
        headers={
            "Cookie": COOKIE,
            "signcode": signcode,
        },
        json=data,
    )
    return response


@rate_limit(calls_per_second=1)
def get_staff(data):
    path = "/saleschannel/qryStaffList"
    signcode = generateSigncode("post", path, data)
    response = requests.post(
        f"https://dealer.unifi.com.my/portal/esales/api{path}",
        headers={
            "Cookie": COOKIE,
            "signcode": signcode,
        },
        json=data,
    )
    return response


def get_all_staff():
    page_number = 1
    results = []

    while True:
        data = {"pageSize": 50, "pageNum": page_number}
        response = get_staff(data)
        result_json = response.json()
        results = [*results, *result_json["data"]]
        if len(result_json["data"]) != data["pageSize"]:
            break
        else:
            page_number += 1
    return results
