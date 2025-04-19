import requests
import time
from functools import wraps
import json
from hashlib import sha256
from urllib.parse import urlencode
import re

COOKIE = "visid_incap_3057414=O7vL8YLNT2e/BUAerwjS9jSP+mcAAAAAQUIPAAAAAAAY6GcEAynMNKgBJbAwlbNx; visid_incap_2993746=DKwY0xq7SKG70Hbq+JYPnAWe+mcAAAAAQUIPAAAAAAA3/+h0pd5NJYtzz5QWI9Ov; INIT_PORTAL=7023; wk8XJKsjpt60BnltX9hNtw===nlCRYGb1gUGYjK0gliqA2A%3D%3D%20utVddUw0Kwe6SEJi3KkuCg%3D%3D; staffJobId=621576; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22600381%22%2C%22first_id%22%3A%221962abf69b0155e-0dcd8098d3d2c5-7e433c49-3686400-1962abf69b12517%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk2MmFiZjY5YjAxNTVlLTBkY2Q4MDk4ZDNkMmM1LTdlNDMzYzQ5LTM2ODY0MDAtMTk2MmFiZjY5YjEyNTE3IiwiJGlkZW50aXR5X2xvZ2luX2lkIjoiNjAwMzgxIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22600381%22%7D%2C%22%24device_id%22%3A%221962f61ba232e8-0f7a6a9d2e908a-7e433c49-3686400-1962f61ba2422b6%22%7D; incap_ses_1671_3057414=ssZmYryLOUaTjvK67ZUwF5n+AGgAAAAAc+ejDtYKlZKTdAAsqIbz0w==; HTML_VERSION=1744883583082; ZSMART_LOCALE=en; areaId=280; orgId=600381; userId=621576; SESSION=f843b7a4-193d-47ce-ab24-e9e5fc8b4c86"

class ApiClient:
    def __init__(self, base_url, api_key=None):
        """
        Initializes the API client with a base URL and optional API key.
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                # Add other default headers if needed
            }
        )
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _get(self, endpoint, params=None):
        """
        Internal method for making GET requests.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request to {url}: {e}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON response from {url}")
            return response.text  # Or handle differently

    def _post(self, endpoint, data=None):
        """
        Internal method for making POST requests.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during POST request to {url}: {e}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON response from {url}")
            return response.text

    def _put(self, endpoint, data=None):
        """
        Internal method for making PUT requests.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during PUT request to {url}: {e}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON response from {url}")
            return response.text

    def _delete(self, endpoint):
        """
        Internal method for making DELETE requests.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return response.status_code
        except requests.exceptions.RequestException as e:
            print(f"Error during DELETE request to {url}: {e}")
            return None


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

@rate_limit(calls_per_second=1)
def get_order_detail(data):
    path = "/cee/order/v2/getCeeOrderDetail"
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

@rate_limit(calls_per_second=1)
def get_staff_detail(data):
    path = "/saleschannel/getStaffDetail"
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
        if len(result_json["data"]) == 0:
            break
        else:
            page_number += 1
    return results
