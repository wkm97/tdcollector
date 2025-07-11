from datetime import datetime
import calendar
import pandas as pd
import typer
from tm.api import get_all_order_list, get_all_staff, get_order_detail

app = typer.Typer()


def get_residential_voice_number(residential_voice_item):
    if "prefix" in residential_voice_item and "accNbr" in residential_voice_item:
        return residential_voice_item["prefix"] + residential_voice_item["accNbr"]
    return None


def process_order(staff, order):
    order_id = order["orderId"]
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
            installation_info_list[0] if len(installation_info_list) > 0 else None
        )
        bundle_items = list(filter(lambda x: x["serviceType"] == 51, order_items))
        internet_items = list(filter(lambda x: x["serviceType"] == 79, order_items))
        residential_voice_items = list(
            filter(lambda x: x["serviceType"] == 80, order_items)
        )
        dms_items = list(filter(lambda x: x["serviceType"] == 924, order_items))
        cloud_storage_item = list(
            filter(lambda x: x["serviceType"] == 888, order_items)
        )
        uni5g_items = list(filter(lambda x: x["serviceType"] == 15, order_items))

        datapoint = {
            "order_id": str(order_detail.get("orderId")),
            "staffName": staff.get("staffName"),
            "status": order_detail.get("stateName"),
            "created_date": order_detail.get("acceptDate"),  # created date
            "updated_date": order_detail.get("stateDate"),  # update date
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
                installation_info.get("appointmentInfo", {}).get("appointmentStartTime")
                if installation_info
                else None
            ),
            "installation_end_time": (
                installation_info.get("appointmentInfo", {}).get("appointmentEndTime")
                if installation_info
                else None
            ),
            "installation_address": (
                installation_info.get("displayAddress") if installation_info else None
            ),
            "customer_name": order_detail.get("custInfo", {}).get("custName"),
            "customer_id_type": order_detail.get("custInfo", {}).get("certTypeName"),
            "customer_id": order_detail.get("custInfo", {}).get("certNbr"),
            "bundle_name": (
                bundle_items[0].get("mainOfferName") if len(bundle_items) > 0 else None
            ),
            "tm_account_id": (
                internet_items[0].get("accNbr") if len(internet_items) > 0 else None
            ),
            "account_nbr": (
                internet_items[0].get("acctNbr") if len(internet_items) > 0 else None
            ),
            "residential_number": (
                get_residential_voice_number(residential_voice_items[0])
                if len(residential_voice_items) > 0
                else None
            ),
            "event_type_name": order_detail.get("eventTypeName"),
            "dms_item": (
                dms_items[0].get("feeList")[0].get("priceName")
                if len(dms_items) > 0
                else None
            ),
            "cloud_storage_item": (
                cloud_storage_item[0].get("feeList")[0].get("priceName")
                if len(cloud_storage_item) > 0
                else None
            ),
            "uni5g_items": uni5g_items[0].get("mainOfferName") if len(uni5g_items) > 0 else None
        }
        return datapoint
    except Exception as e:
        print(staff)
        print(order_id)
        raise e


@app.command()
def ongoing():
    print("-------------RESULT----------------")
    data = []
    staffs = get_all_staff()
    # staffs = filter(lambda x: x["staffId"] in [621433, 621414, 621576], staffs)
    for idx, staff in enumerate(staffs):
        # get_staff_detail_response = get_staff_detail(
        #     {"staffId": staff["staffId"], "staffCode": staff["staffCode"]}
        # )
        # staff_detail = get_staff_detail_response.json()["data"]

        # get_order_list_response = get_order_list(get_order_list_data)

        all_order = get_all_order_list(staff["staffId"], "Y")

        print(idx, staff["staffId"], staff["staffName"], len(all_order))
        for order in all_order:
            datapoint = process_order(staff=staff, order=order)
            data.append(datapoint)

    df = pd.DataFrame(data)
    df = df.set_index("order_id")
    df.to_excel("ongoing.xlsx")
    print(df)


@app.command()
def historical(year: int, month: int):
    print("-------------RESULT----------------")
    if year < 2025 or year > 2100:
        raise Exception("Year must be in between 2025 and 2100")
    if month < 1 or month > 12:
        raise Exception("Month must be in between 1 and 12")
    target = datetime(year, month, 1)
    month_range = calendar.monthrange(year, month)
    createdDateFrom = target.strftime("%Y%m") + "01000000"
    # createdDateTo = datetime.today().strftime("%Y%m%d%H%M%S")
    createdDateTo = target.strftime("%Y%m") + str(month_range[1]) + "235959"
    print(createdDateFrom, createdDateTo)
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
        all_order = get_all_order_list(
            staff["staffId"], "N", createdDateFrom, createdDateTo
        )

        print(idx, staff["staffId"], staff["staffName"], len(all_order))

        for order in all_order:
            datapoint = process_order(staff=staff, order=order)
            data.append(datapoint)

    df = pd.DataFrame(data)
    df = df.set_index("order_id")
    df.to_excel("historical.xlsx")
    print(df)


if __name__ == "__main__":
    app()
