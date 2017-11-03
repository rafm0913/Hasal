import os
import copy
import json
import socket
import shutil
import datetime
import logging
from lib.common.b2Util import B2Util
from lib.common.commonUtil import CommonUtil
from lib.common.statusFileCreator import StatusFileCreator


def status_json_creator(**kwargs):
    """
    Job Function for status json creator
    @param kwargs:
    @return:
     data example:
    # status json format
    # host_name.json
    # {
    "data":[
        {
            "type": "interactive",
            "start_ts": "1234567890",
            "cmd": "interactive",
            "status": [
                {
                    "code": "100",
                    "status_code_desc": "Get command from interactive mode",
                    "utc_timestamp": "1234567898"
                },
                {
                    "code": "200",
                    "status_code_desc": "Get command from interactive mode",
                    "utc_timestamp": "1234567899"
                },
                {
                    "code": "900",
                    "status_code_desc": "Get command from interactive mode",
                    "utc_timestamp": "1234567900"
                }
            ]
        },
        {
            "type": "interactive",
            "start_ts": "2345678901",
            "cmd": "interactive",
            "status": [
                {
                    "code": "100",
                    "status_code_desc": "Get command from interactive mode",
                    "utc_timestamp": "1234567898"
                },
                {
                    "code": "300",
                    "status_code_desc": "Get command from interactive mode",
                    "utc_timestamp": "1234567899"
                }
            ]
        },
        {
            "type": "interactive",
            "start_ts": "3456789012",
            "cmd": "interactive",
            "status": [
                {
                    "code": "100",
                    "status_code_desc": "Get command from interactive mode",
                    "utc_timestamp": "1234567898"
                }
            ]
        }
    ]
}
    #                           }
    #            }
    #  }

    """
    DEFAULT_DATA_RECENTLY_DEFINE_PERIOD = 7
    DEFAULT_DATA_HISTORY_DEFINE_PERIOD = 30

    # check configs in kwargs
    if "configs" not in kwargs:
        raise Exception("The current input consumer kwargs didn't contain the kwarg [configs]")

    # get config defined parameter [data period define]
    b2_account_id = kwargs['configs'].get("b2_account_id", None)
    b2_account_key = kwargs['configs'].get("b2_account_key", None)
    b2_upload_bucket_name = kwargs['configs'].get("b2_upload_bucket_name", None)
    data_recently_define_period = kwargs['configs'].get("data_recently_define_period", DEFAULT_DATA_RECENTLY_DEFINE_PERIOD)
    data_history_define_period = kwargs['configs'].get("data_recently_define_period", DEFAULT_DATA_HISTORY_DEFINE_PERIOD)

    # get status folder path, status json file name and path
    status_folder_path = StatusFileCreator.get_status_folder()
    current_host_name = socket.gethostname()
    recently_status_json_file_name = "%s_recently.json" % current_host_name
    history_status_json_file_name = "%s_history.json" % current_host_name
    recently_status_json_file_path = os.path.join(status_folder_path, recently_status_json_file_name)
    history_status_json_file_path = os.path.join(status_folder_path, history_status_json_file_name)

    # housekeeping the status folder before generating the status json file
    status_folder_list = [folder_name for folder_name in os.listdir(status_folder_path) if folder_name.startswith(".") is False and CommonUtil.represent_as_int(folder_name.split("-")[1])]
    current_utc_time = datetime.datetime.utcnow()
    outdated_date = current_utc_time - datetime.timedelta(days=data_history_define_period)
    outdated_status_folder_list = [folder_name for folder_name in status_folder_list if datetime.datetime.utcfromtimestamp(int(folder_name.split("-")[1])) < outdated_date]
    for outdated_folder_name in outdated_status_folder_list:
        outdated_folder_path = os.path.join(status_folder_path, outdated_folder_name)
        shutil.rmtree(outdated_folder_path)
        logging.debug("Housekeeping outdated folder [%s]" % outdated_folder_path)

    # generate history period json obj
    history_status_json_obj = {"data": []}
    history_reference_data_table = {}

    # load exisitng history status json file
    if os.path.exists(history_status_json_file_path):
        try:
            with open(history_status_json_file_path) as read_history_status_json_fh:
                history_reference_obj = json.load(read_history_status_json_fh)

                # convert existing data to reference table
                if len(history_reference_obj["data"]) > 0:
                    for data_obj in history_reference_obj["data"]:
                        job_name = data_obj["type"]
                        job_utc_ts = data_obj["start_ts"]
                        task_name = data_obj["cmd"]
                        for status_obj in data_obj["status"]:
                            status_code = status_obj["code"]
                            if job_name in history_reference_data_table:
                                if job_utc_ts in history_reference_data_table[job_name]:
                                    if task_name in history_reference_data_table[job_name][job_utc_ts]:
                                        if status_code in history_reference_data_table[job_name][job_utc_ts][task_name]:
                                            logging.error("Skip inject job obj into reference due to status code duplicated!!!, job_name:[%s], job_utc_ts:[%s], task_name:[%s], status_code:[%s]" % (job_name, job_utc_ts, task_name, status_code))
                                        else:
                                            history_reference_data_table[job_name][job_utc_ts][task_name][
                                                status_code] = status_obj
                                    else:
                                        history_reference_data_table[job_name][job_utc_ts][task_name] = {
                                            status_code: status_obj}
                                else:
                                    history_reference_data_table[job_name][job_utc_ts] = {
                                        task_name: {status_code: status_obj}}
                            else:
                                history_reference_data_table[job_name] = {
                                    job_utc_ts: {task_name: {status_code: status_obj}}}
        except Exception, e:
            logging.error(
                "Load history status json file[%s] with error [%s]" % (history_status_json_file_path, e.message))

    # generate status json obj
    history_status_folder_list = [folder_name for folder_name in os.listdir(status_folder_path) if folder_name.startswith(".") is False and CommonUtil.represent_as_int(folder_name.split("-")[1])]
    for history_status_folder_name in history_status_folder_list:
        history_status_folder_path = os.path.join(status_folder_path, history_status_folder_name)
        job_name = history_status_folder_name.split("-")[0]
        job_utc_timestamp_string = history_status_folder_name.split("-")[1]
        task_file_name_list = [task_file_name for task_file_name in os.listdir(history_status_folder_path) if task_file_name.startswith(".") is False and CommonUtil.represent_as_int(task_file_name.split("-")[0])]
        task_with_extname_list = list(set([task_file_name.split("-")[1] for task_file_name in task_file_name_list]))
        for task_with_extname in task_with_extname_list:
            task_name = task_with_extname.split(os.extsep)[0]
            data_obj = {"type": job_name,
                        "start_ts": job_utc_timestamp_string,
                        "cmd": task_name,
                        "status": []}
            task_code_file_list = [task_file_name for task_file_name in task_file_name_list if task_file_name.split("-")[1].split(os.extsep)[0] == task_name]
            for task_code_file_name in task_code_file_list:
                task_code = task_code_file_name.split("-")[0]
                history_reference_data = history_reference_data_table.get(job_name, {}).get(job_utc_timestamp_string, {}).get(task_name, {}).get(task_code, None)
                if history_reference_data:
                    data_obj["status"].append(history_reference_data)
                else:
                    task_code_file_path = os.path.join(history_status_folder_path, task_code_file_name)
                    task_code_obj = CommonUtil.load_json_file(task_code_file_path)
                    task_code_obj["code"] = task_code
                    data_obj["status"].append(task_code_obj)
            history_status_json_obj["data"].append(data_obj)

    # dump history json obj to file
    with open(history_status_json_file_path, "wb") as history_write_fh:
        json.dump(history_status_json_obj, history_write_fh)

    # generate recently period json obj
    recently_status_json_obj = {"data": []}
    recently_date = current_utc_time - datetime.timedelta(days=data_recently_define_period)
    for recently_job_obj in history_status_json_obj["data"]:
        if recently_date <= datetime.datetime.utcfromtimestamp(int(recently_job_obj["start_ts"])):
            recently_status_json_obj["data"].append(copy.deepcopy(recently_job_obj))

    # dump recently json obj to file
    with open(recently_status_json_file_path, "wb") as recently_write_fh:
        json.dump(recently_status_json_obj, recently_write_fh)

    # upload to b2
    b2_obj = B2Util(b2_account_id, b2_account_key)
    history_status_json_url = b2_obj.upload_file(history_status_json_file_path, b2_upload_bucket_name)
    recently_status_json_url = b2_obj.upload_file(recently_status_json_file_path, b2_upload_bucket_name)

    if not history_status_json_url:
        logging.error("Upload history status json file failed!")

    if not recently_status_json_url:
        logging.error("Upload recently status json file failed!")

    if history_status_json_url and recently_status_json_url:
        logging.debug("Upload history and recently status json file success!!")