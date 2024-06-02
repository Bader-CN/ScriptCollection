#!/usr/bin/python3
# -*- coding: UTF-8 -*-

########################################################################################################################
#   author: zhanghong.personal@outlook.com
#  version: 1.2
#    usage: salesforce_month_report.py [month offset, like -1, -2, -3...] [-debug]
# release nodes:
#   2024.05.07 - first release
#   2024.05.15 - add debug function and change algorithms
#   2024.05.16 - change DTR related algorithms
########################################################################################################################

import re
import os
import sys
import pandas as pd
from prettytable import PrettyTable

# 定义全局变量
table = PrettyTable()
summary_data = []
report_cases = None
report_survy = None
report_miss_cases = []
report_miss_survy = []
open_cases_by_month = None
clos_cases_by_month = None

# 定义偏移量, 如果不写默认是 0
# noinspection PyBroadException
try:
    month_offset = int(sys.argv[1])
except:
    month_offset = 0

# 是否开启 debug
debug = False
for key in sys.argv:
    if key == "-debug":
        debug = True


def show_debug(filename, pdata, columns=None):
    """
    debug 输出的原始数据
    :param filename: 输出的文件名
    :param pdata: pandas 数据
    :param columns: 输出那些列, 默认输出所有列, 接受的是列表形式的数据
    :return:
    """
    if debug:
        if columns is not None:
            pdata = pdata[columns]
        pdata = pdata.reset_index(drop=True)
        pdata.index = pdata.index + 1

        if os.path.exists(r".\debug") is False:
            os.mkdir(r".\debug")
        pdata.to_csv(r".\debug\{}".format(filename))


# 计算指定的年月
if pd.Timestamp.now().month + month_offset >= 1:
    y_offset = pd.Timestamp.now().year
    m_offset = pd.Timestamp.now().month + month_offset
elif pd.Timestamp.now().month + month_offset == 0:
    y_offset = pd.Timestamp.now().year - 1
    m_offset = 12
elif pd.Timestamp.now().month + month_offset > -12:
    y_offset = pd.Timestamp.now().year - 1
    m_offset = 12 - (abs(pd.Timestamp.now().month + month_offset) % 12)
else:
    y_offset = pd.Timestamp.now().year - (abs(pd.Timestamp.now().month + month_offset) // 12) - 1
    m_offset = 12 - (abs(pd.Timestamp.now().month + month_offset) % 12)

# 生成表头
table.field_names = ["KPI", "{}-{}".format(str(y_offset), str(m_offset))]

# 检查原始报告是否符合要求
for i in os.listdir(os.path.abspath("./")):
    if re.findall(r"report\d+.csv", i, re.IGNORECASE):
        with open(i, mode="r", encoding="utf-8") as f:
            heads = f.readline().strip().replace('"', '').split(",")
            # 检查是否符合 cases 报告
            head_by_cases = [
                "Case Owner",
                "Case Number",
                "Date/Time Opened",
                # "Closed Date",
                "Date/Time Closed",
                "Age (Days)",
                "Suggested_Solution_Date",
                "Status", "Knowledge Base Article",
                "Idol Knowledge Link",
                "R&D Incident",
                "Escalated",
            ]
            head_by_survy = [
                "Case Owner",
                "Case Number",
                # "Closed Data",
                "Customer Feed Back Survey: Last Modified Date",
                "OpenText made it easy to handle my case",
                "Satisfied with support experience",
            ]
            if all(x in heads for x in head_by_cases):
                report_cases = i
            if all(x in heads for x in head_by_survy):
                report_survy = i

# 分析 Cases Report
if report_cases is None:
    print("[WARN] Case report miss columns, will ignore.")
else:
    rawcase = pd.read_csv(report_cases)
    # 数据预处理
    rawcase["Date/Time Opened"] = pd.to_datetime(rawcase["Date/Time Opened"], format="%Y-%m-%d %p%I:%M")
    rawcase["Date/Time Closed"] = pd.to_datetime(rawcase["Date/Time Closed"], format="%Y-%m-%d %p%I:%M")
    rawcase["Suggested_Solution_Date"] = pd.to_datetime(rawcase["Suggested_Solution_Date"], format="%Y-%m-%d %p%I:%M")
    # 根据年份和月份筛选数据
    open_cases_y = rawcase[rawcase["Date/Time Opened"].dt.year == y_offset]
    open_cases_m = open_cases_y[open_cases_y["Date/Time Opened"].dt.month == m_offset]
    close_cases_y = rawcase[rawcase["Date/Time Closed"].dt.year == y_offset]
    close_cases_m = close_cases_y[close_cases_y["Date/Time Closed"].dt.month == m_offset]
    # 赋值给共享变量, 这些值会用于其他的报表
    if len(open_cases_m) != 0:
        open_cases_by_month = open_cases_m
    if len(close_cases_m) != 0:
        clos_cases_by_month = close_cases_m
    # 计算当前状态下状态为非 Closed 的 cases
    # 下个月开始时间点为 pd.Timestamp(y_offset, m_offset, 1) + pd.offsets.MonthEnd() + pd.offsets.DateOffset()
    backlog = rawcase[rawcase["Status"] != "Closed"]
    backlog = backlog[backlog["Date/Time Opened"] < pd.Timestamp(y_offset, m_offset, 1) + pd.offsets.MonthEnd() + pd.offsets.DateOffset()]
    backlog_history = rawcase[rawcase["Status"] == "Closed"]
    backlog_history = backlog_history[backlog_history["Date/Time Closed"] >= pd.to_datetime("{}-{}".format(y_offset, m_offset, 1), format="%Y-%m") + pd.offsets.MonthEnd() + pd.offsets.DateOffset()]
    backlog_history = backlog_history[backlog_history["Date/Time Opened"] < pd.Timestamp(y_offset, m_offset, 1) + pd.offsets.MonthEnd() + pd.offsets.DateOffset()]
    backlog_total = pd.concat([backlog, backlog_history])
    # KCS 相关
    kcs_all = close_cases_m[close_cases_m["Knowledge Base Article"].notna() | close_cases_m["Idol Knowledge Link"].notna()]
    show_debug("Cases_by_KCS.csv", kcs_all, columns=["Case Owner", "Case Number", "Status", "Knowledge Base Article", "Idol Knowledge Link"])
    # 分析数据并得出结果
    summary_data.append(["Open Cases", len(open_cases_m)])
    summary_data.append(["Close Cases", len(close_cases_m)])
    show_debug("Cases_by_Open_on_month.csv", open_cases_m, columns=["Case Owner", "Case Number", "Status", "Date/Time Opened"])
    show_debug("Cases_by_Close_on_month.csv", close_cases_m, columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Date/Time Closed"])
    # Closure Rate
    if len(open_cases_m) != 0:
        summary_data.append(["Closure Rate", (str(round(len(close_cases_m) / len(open_cases_m) * 100, 2)) + "%")])
    else:
        summary_data.append(["Closure Rate", "-"])
    # R&D Assist Rate
    if len(close_cases_m) != 0:
        summary_data.append(["R&D Assist Rate", str(round(len(close_cases_m[close_cases_m["R&D Incident"].notna()]) / len(close_cases_m) * 100, 2)) + "%"])
        show_debug("Cases_by_R&D_Incident.csv", close_cases_m[close_cases_m["R&D Incident"].notna()], columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Date/Time Closed", "R&D Incident"])
    else:
        summary_data.append(["R&D Assist Rate", "-"])
    # Backlog
    summary_data.append(["Backlog", len(backlog_total)])
    show_debug("Cases_by_Backlog.csv", backlog_total, columns=["Case Owner", "Case Number", "Status", "Date/Time Opened"])
    # Backlog 相关百分比的计算
    # 必须是当月才会计算, 并且 backlog 的值要求大于 0
    if month_offset == 0 and (len(backlog_total)) >= 0:
        # Backlog > 30 的比例
        backlog30_percentage = str(round(len(backlog[backlog["Age (Days)"] > 30.0]) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        show_debug("Cases_by_Backlog_ge_30.csv", backlog[backlog["Age (Days)"] > 30.0], columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Age (Days)"])
        summary_data.append(["Backlog > 30", backlog30_percentage])
        # Backlog > 30 并且没有升级的比例
        backlog30_no_cpe = backlog[backlog["Age (Days)"] > 30.0]
        backlog30_no_cpe = backlog30_no_cpe[backlog30_no_cpe["R&D Incident"].isna()]
        show_debug("Cases_by_Backlog_ge_30_noCPE.csv", backlog30_no_cpe, columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Age (Days)"])
        backlog_30_no_cpe = str(round(len(backlog30_no_cpe) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        summary_data.append(["Backlog > 30 (Support)", backlog_30_no_cpe])
        # Backlog > 90 的比例
        backlog90_percentage = str(round(len(backlog[backlog["Age (Days)"] > 90.0]) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        show_debug("Cases_by_Backlog_ge_90.csv", backlog[backlog["Age (Days)"] > 90.0], columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Age (Days)"])
        summary_data.append(["Backlog > 90", backlog90_percentage])
        # DTR 计算
        # 未关闭的 case, 分为设置过 SS 和未设置过 SS
        ssdata_bl_ss = backlog[backlog["Suggested_Solution_Date"].notna()]
        ssdata_bl_noss = backlog[backlog["Suggested_Solution_Date"].isna()]
        # 当月开的 case, 分为设置过 SS 和未设置过 SS
        ssdata_mo_ss = open_cases_m[open_cases_m["Suggested_Solution_Date"].notna()]
        ssdata_mo_noss = open_cases_m[open_cases_m["Suggested_Solution_Date"].isna()]
        # 合并所有数据并去重
        all_data = pd.concat([ssdata_bl_ss, ssdata_bl_noss, ssdata_mo_ss, ssdata_mo_noss])
        all_data.sort_values(by=["Case Number"], ascending=False)
        all_data.drop_duplicates(subset="Case Number")
        # 基于是否设置过 SS 来拆分数据, 此时已经不存在重复的数据了
        ss_data = all_data[all_data["Suggested_Solution_Date"].notna()]
        ns_data = all_data[all_data["Suggested_Solution_Date"].isna()]
        if len(ss_data) != 0 or len(ns_data) != 0:
            dtr_ss_data = pd.DataFrame()
            # SS 相关的时间
            dtr_ss_data["Date/Time Opened"] = pd.to_datetime(ss_data["Date/Time Opened"]).dt.date
            dtr_ss_data["Suggested_Solution_Date"] = pd.to_datetime(ss_data["Suggested_Solution_Date"]).dt.date
            dtr_ss = dtr_ss_data["Suggested_Solution_Date"] - dtr_ss_data["Date/Time Opened"]
            # 非 SS 的时间
            dtr_ns = ns_data["Age (Days)"]
            # 计算 DTR
            dtr_avg = (dtr_ss.sum().days + dtr_ns.sum()) / len(all_data)
            dtr_avg = str(round(dtr_avg, 2))
            summary_data.append(["DTR", dtr_avg])
            show_debug("Cases_by_DTR.csv", all_data, columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Suggested_Solution_Date", "R&D Incident", "Age (Days)"])
        else:
            summary_data.append(["DTR", "-"])
        # DTR only Support
        all_data_os = all_data[all_data["R&D Incident"].isna()]
        # 分为设置过 SS 的和没设置过 SS 的
        ss_data_os = all_data_os[all_data_os["Suggested_Solution_Date"].notna()]
        ns_data_os = all_data_os[all_data_os["Suggested_Solution_Date"].isna()]
        if len(ss_data_os) != 0 or len(ns_data_os) != 0:
            dtr_ss_data_os = pd.DataFrame()
            # SS 相关的时间
            dtr_ss_data_os["Date/Time Opened"] = pd.to_datetime(ss_data_os["Date/Time Opened"]).dt.date
            dtr_ss_data_os["Suggested_Solution_Date"] = pd.to_datetime(ss_data_os["Suggested_Solution_Date"]).dt.date
            dtr_ss_os = dtr_ss_data_os["Suggested_Solution_Date"] - dtr_ss_data_os["Date/Time Opened"]
            # 非 SS 的时间
            dtr_ns_os = ns_data_os["Age (Days)"]
            # 计算 DTR
            dtr_avg_os = (dtr_ss_os.sum().days + dtr_ns_os.sum()) / len(all_data)
            dtr_avg_os = str(round(dtr_avg_os, 2))
            summary_data.append(["DTR Support only", dtr_avg_os])
            show_debug("Cases_by_DTR_only_Support.csv", all_data_os, columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Suggested_Solution_Date", "R&D Incident", "Age (Days)"])
        else:
            summary_data.append(["DTR Support only", "-"])
    else:
        summary_data.append(["Backlog > 30", "-"])
        summary_data.append(["Backlog > 30 (Support)", "-"])
        summary_data.append(["Backlog > 90", "-"])
        summary_data.append(["DTR", "-"])
    # Backlog Index
    if len(open_cases_m) != 0:
        summary_data.append(["Backlog Index", str(round(len(backlog) / len(open_cases_m) * 100, 2)) + "%"])
    else:
        summary_data.append(["Backlog Index", "-"])
    # KCS Linkage
    if len(close_cases_m) != 0:
        summary_data.append(["KCS Linkage", str(round(len(kcs_all) / len(close_cases_m) * 100, 2)) + "%"])
    else:
        summary_data.append(["KCS Linkage", "-"])
    # Escalated
    if len(open_cases_m) != 0:
        summary_data.append(["Escalated", str(len(open_cases_m[open_cases_m.Escalated != 0]))])
        show_debug("Cases_by_Escalated.csv", open_cases_m[open_cases_m.Escalated != 0], columns=["Case Owner", "Case Number", "Status", "Date/Time Opened", "Escalated"])

# 分析 Survey Report
if report_survy is None:
    print("[WARN] Survey report miss columns, will ignore.")
else:
    rawsurv = pd.read_csv(report_survy)
    # 数据预处理
    rawsurv["Customer Feed Back Survey: Last Modified Date"] = pd.to_datetime(rawsurv["Customer Feed Back Survey: Last Modified Date"], format="%Y-%m-%d")
    # rawsurv["Closed Data"] = pd.to_datetime(rawsurv["Closed Data"], format="%Y-%m-%d")
    rawsurv = rawsurv.sort_values(by=["Customer Feed Back Survey: Last Modified Date", ], ascending=False)
    rawsurv = rawsurv.drop_duplicates(subset="Case Number")
    # 根据年份和月份筛选数据
    survey_y = rawsurv[rawsurv["Customer Feed Back Survey: Last Modified Date"].dt.year == y_offset]
    survey_m = survey_y[survey_y["Customer Feed Back Survey: Last Modified Date"].dt.month == m_offset]
    survey_ces = survey_m[survey_m["OpenText made it easy to handle my case"] >= 8.0]
    survey_cast = survey_m[survey_m["Satisfied with support experience"] >= 8.0]
    # Survey CES & Survey CAST
    if len(survey_m) > 0:
        summary_data.append(["Survey CES", str(round(len(survey_ces) / len(survey_m) * 100, 2)) + "%"])
        summary_data.append(["Survey CAST", str(round(len(survey_cast) / len(survey_m) * 100, 2)) + "%"])
        show_debug("Survey_CES_ge_8_by_month.csv", survey_ces, columns=["Case Owner", "Case Number", "OpenText made it easy to handle my case"])
        show_debug("Survey_CAST_ge_8_by_month.csv", survey_ces, columns=["Case Owner", "Case Number", "Satisfied with support experience"])
    else:
        summary_data.append(["Survey CES", "-"])
        summary_data.append(["Survey CAST", "-"])
    # SRR (Survey Response Rate)
    if len(survey_m) > 0 and clos_cases_by_month is not None:
        summary_data.append(["Survey Response Rate", str(round(len(survey_m) / len(clos_cases_by_month) * 100, 2)) + "%"])
    else:
        summary_data.append(["Survey Response Rate", "-"])

# 将结果写入到文件中
if report_cases is not None or report_survy is not None:
    output_file = "{}-{}".format(str(y_offset), str(m_offset)) + ".csv"
    df = pd.DataFrame(summary_data, columns=summary_data[0])
    df.to_csv(output_file, index=False, header=["KPI", "{}-{}".format(str(y_offset), str(m_offset))])

    # 打印结果
    table.add_rows(summary_data)
    print(table)
