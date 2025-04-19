import pandas as pd
from tm.api import (
    get_all_staff,
    get_order_detail,
    get_order_list
)


def main():
    for i in range(5):
        print("------------------")

def get_residential_voice_number(residential_voice_item):    
    if "prefix" in residential_voice_item and "accNbr" in residential_voice_item:
        return residential_voice_item["prefix"] + residential_voice_item["accNbr"]
    return None

if __name__ == "__main__":
    print("-------------RESULT----------------")
    data = []
    staffs = get_all_staff()
    # staffs = filter(lambda x: x["staffId"] in [621433, 621414, 621576], staffs)
    for idx, staff in enumerate(staffs):
        # get_staff_detail_response = get_staff_detail(
        #     {"staffId": staff["staffId"], "staffCode": staff["staffCode"]}
        # )
        # staff_detail = get_staff_detail_response.json()["data"]
        get_order_list_data = {
            "dPartyCode": staff["staffId"],
            "pageSize": 50,
            "onWayFlag": "Y",
            "pageNum": 1,
            "dPartyType": "E",
            "extData": {"senario": "esales-monthly-order"},
        }
        get_order_list_response = get_order_list(get_order_list_data)
        get_order_list_result = get_order_list_response.json()


        print(
            idx,
            staff["staffId"],
            staff["staffName"],
            get_order_list_response.ok,
            get_order_list_result["code"],
            get_order_list_result["total"],
        )

        if (
            get_order_list_result["code"] == "200"
            and get_order_list_result["total"] > 0
        ):
            for order in get_order_list_result["data"]:
                order_id = order["orderId"]
                order_nbr = order["orderNbr"]
                get_order_detail_data = {
                    "custOrderId": order["orderId"],
                    "custOrderNbr": order["orderNbr"],
                }
                get_order_detail_response = get_order_detail(get_order_detail_data)
                order_detail = get_order_detail_response.json()["data"]
                order_items = order_detail["orderItemList"]
                installation_info_list = order_detail["installationInfoList"]
                
                try:
                    if len(installation_info_list) != 1:
                        print("WARNING: NO INSTALLATION POSSIBLE")
                        continue

                    installation_info = installation_info_list[0]
                    bundle_item = list(filter(lambda x: x["serviceType"] == 51, order_items))[0]
                    internet_item = list(filter(lambda x: x["serviceType"] == 79, order_items))[0]
                    residential_voice_item = list(filter(lambda x: x["serviceType"] == 80, order_items))[0]

                    datapoint = {
                        "order_id": str(order_detail["orderId"]),
                        "staffName": staff["staffName"],
                        "status": order_detail["stateName"],
                        "created_date": order_detail["acceptDate"], # created date
                        "update_date": order_detail["stateDate"], # update date
                        "installation_contact_name": installation_info["custContactDto"]["contactName"] if "custContactDto" in installation_info and "contactName" in installation_info["custContactDto"] else None,
                        "installation_contact_email": installation_info["custContactDto"]["email"] if "custContactDto" in installation_info and "email" in installation_info["custContactDto"] else None,
                        "installation_contact_phone": installation_info["custContactDto"]["contactNbr"] if "custContactDto" in installation_info else None,
                        "installation_start_time": installation_info["appointmentInfo"]["appointmentStartTime"] if "appointmentStartTime" in installation_info["appointmentInfo"] else None,
                        "installation_end_time": installation_info["appointmentInfo"]["appointmentEndTime"] if "appointmentEndTime" in installation_info["appointmentInfo"] else None,
                        "installation_address": installation_info["displayAddress"] if "displayAddress" in installation_info else None,
                        "customer_name": order_detail["custInfo"]["custName"] if "custInfo" in order_detail and "custName" in order_detail["custInfo"] else None,
                        "customer_id_type": order_detail["custInfo"]["certTypeName"] if "custInfo" in order_detail and "certTypeName" in order_detail["custInfo"] else None,
                        "customer_id": order_detail["custInfo"]["certNbr"] if "custInfo" in order_detail and "certNbr" in order_detail["custInfo"] else None,
                        "bundle_name": bundle_item["mainOfferName"],
                        "tm_account_id": internet_item["accNbr"],
                        "account_nbr": internet_item["acctNbr"],
                        "residential_number": get_residential_voice_number(residential_voice_item)
                    }
                    data.append(datapoint)
                except Exception as e:
                    print(staff)
                    print(order_id)
                    raise e
    
    df = pd.DataFrame(data)
    df = df.set_index('order_id')
    df.to_excel('data.xlsx')
    print(df)