import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tm.api import get_all_order_list, get_all_staff, get_order_detail, get_order_list


def main():
    for i in range(5):
        print("------------------")


def get_residential_voice_number(residential_voice_item):
    if "prefix" in residential_voice_item and "accNbr" in residential_voice_item:
        return residential_voice_item["prefix"] + residential_voice_item["accNbr"]
    return None


if __name__ == "__main__":
    print("-------------RESULT----------------")
    print((datetime.today() - relativedelta(months=2)).strftime("%Y%m") + "01000000")
    data = []
    staffs = get_all_staff()
    # staffs = filter(lambda x: x["staffId"] in [621394], staffs)
    for idx, staff in enumerate(staffs):
        # get_staff_detail_response = get_staff_detail(
        #     {"staffId": staff["staffId"], "staffCode": staff["staffCode"]}
        # )
        # staff_detail = get_staff_detail_response.json()["data"]

        # get_order_list_response = get_order_list(get_order_list_data)
        # get_order_list_result = get_order_list_response.json()
        createdDateFrom = (datetime.today() - relativedelta(months=2)).strftime(
            "%Y%m"
        ) + "01000000"
        createdDateTo = datetime.today().strftime("%Y%m%d%H%M%S")
        all_order = get_all_order_list(
            staff["staffId"], "N", createdDateFrom, createdDateTo
        )

        print(idx, staff["staffId"], staff["staffName"], len(all_order))

        for order in all_order:
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
                    print(
                        f"WARNING: NO INSTALLATION POSSIBLE for {staff["staffName"]} - {order_detail.get("orderId")}"
                    )

                installation_info = (
                    installation_info_list[0]
                    if len(installation_info_list) > 0
                    else None
                )
                bundle_items = list(
                    filter(lambda x: x["serviceType"] == 51, order_items)
                )
                internet_items = list(
                    filter(lambda x: x["serviceType"] == 79, order_items)
                )
                residential_voice_items = list(
                    filter(lambda x: x["serviceType"] == 80, order_items)
                )

                datapoint = {
                    "order_id": str(order_detail.get("orderId")),
                    "staffName": staff.get("staffName"),
                    "status": order_detail.get("stateName"),
                    "created_date": order_detail.get("acceptDate"),  # created date
                    "update_date": order_detail.get("stateDate"),  # update date
                    "installation_contact_name": (
                        installation_info.get("custContactDto", {}).get("contactName")
                        if installation_info
                        else None
                    ),
                    "installation_contact_email": (
                        installation_info.get("custContactDto", {}).get("email")
                        if installation_info
                        else None
                    ),
                    "installation_contact_phone": (
                        installation_info.get("custContactDto", {}).get("contactNbr")
                        if installation_info
                        else None
                    ),
                    "installation_start_time": (
                        installation_info.get("appointmentInfo", {}).get(
                            "appointmentStartTime"
                        )
                        if installation_info
                        else None
                    ),
                    "installation_end_time": (
                        installation_info.get("appointmentInfo", {}).get(
                            "appointmentEndTime"
                        )
                        if installation_info
                        else None
                    ),
                    "installation_address": (
                        installation_info.get("displayAddress")
                        if installation_info
                        else None
                    ),
                    "customer_name": order_detail.get("custInfo", {}).get("custName"),
                    "customer_id_type": order_detail.get("custInfo", {}).get(
                        "certTypeName"
                    ),
                    "customer_id": order_detail.get("custInfo", {}).get("certNbr"),
                    "bundle_name": (
                        bundle_items[0].get("mainOfferName")
                        if len(bundle_items) > 0
                        else None
                    ),
                    "tm_account_id": (
                        internet_items[0].get("accNbr")
                        if len(internet_items) > 0
                        else None
                    ),
                    "account_nbr": (
                        internet_items[0].get("acctNbr")
                        if len(internet_items) > 0
                        else None
                    ),
                    "residential_number": (
                        get_residential_voice_number(residential_voice_items[0])
                        if len(residential_voice_items) > 0
                        else None
                    ),
                }
                data.append(datapoint)
            except Exception as e:
                print(staff)
                print(order_id)
                raise e

    df = pd.DataFrame(data)
    df = df.set_index("order_id")
    df.to_excel("data.xlsx")
    print(df)
