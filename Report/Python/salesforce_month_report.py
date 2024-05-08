#!/usr/bin/python3
# -*- coding: UTF-8 -*-

########################################################################################################################
#   author: zhanghong.personal@outlook.com
#  version: 1.1
#    usage: salesforce_month_report.py [month offset, like -1, -2, -3...]
# release nodes:
#   2024.05.07 - first release
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
open_cases_by_month = None
clos_cases_by_month = None

# 定义偏移量, 如果不写默认是 0
try:
    month_offset = int(sys.argv[1])
except:
    month_offset = 0

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
            if all(x in heads for x in ["Case Number", "Date/Time Opened", "Closed Date", "Suggested_Solution_Date", "Status", "Knowledge Base Article", "Idol Knowledge Link", "R&D Incident", "Escalated"]):
                report_cases = i
            if all(x in heads for x in ["Customer Feed Back Survey: Last Modified Date", "Closed Data", "OpenText made it easy to handle my case", "Satisfied with support experience"]):
                report_survy = i

# 分析 Cases Report
if report_cases is not None:
    rawcase = pd.read_csv(report_cases)
    # 数据预处理
    rawcase["Date/Time Opened"] = pd.to_datetime(rawcase["Date/Time Opened"], format="%Y-%m-%d %p%I:%M")
    rawcase["Suggested_Solution_Date"] = pd.to_datetime(rawcase["Suggested_Solution_Date"], format="%Y-%m-%d %p%I:%M")
    rawcase["Closed Date"] = pd.to_datetime(rawcase["Closed Date"], format="%Y-%m-%d")
    # 根据年份和月份筛选数据
    open_cases_y = rawcase[rawcase["Date/Time Opened"].dt.year == y_offset]
    open_cases_m = open_cases_y[open_cases_y["Date/Time Opened"].dt.month == m_offset]
    close_cases_y = rawcase[rawcase["Closed Date"].dt.year == y_offset]
    close_cases_m = close_cases_y[close_cases_y["Closed Date"].dt.month == m_offset]
    # 赋值给共享变量, 这些值会用于其他的报表
    if len(open_cases_m) != 0:
        open_cases_by_month = open_cases_m
    if len(close_cases_m) != 0:
        clos_cases_by_month = close_cases_m
    # 计算当前状态下状态为非 Closed 的 cases
    backlog = rawcase[rawcase["Status"] != "Closed"]
    backlog = backlog[backlog["Date/Time Opened"] <= pd.Timestamp(y_offset, m_offset, 1) + pd.offsets.MonthEnd()]
    backlog_history = rawcase[rawcase["Status"] == "Closed"]
    backlog_history = backlog_history[backlog_history["Closed Date"] > pd.to_datetime("{}-{}".format(y_offset, m_offset, 1), format="%Y-%m") + pd.offsets.MonthEnd()]
    backlog_history = backlog_history[backlog_history["Date/Time Opened"] <= pd.Timestamp(y_offset, m_offset, 1) + pd.offsets.MonthEnd()]
    
    # KCS 相关
    kcs_all = close_cases_m[close_cases_m["Knowledge Base Article"].notna() | close_cases_m["Idol Knowledge Link"].notna()]
    # 分析数据并得出结果
    summary_data.append(["Open Cases", len(open_cases_m)])
    summary_data.append(["Close Cases", len(close_cases_m)])
    # Closure Rate
    if len(open_cases_m) != 0:
        summary_data.append(["Closure Rate", (str(round(len(close_cases_m) / len(open_cases_m) * 100, 2)) + "%")])
    else:
        summary_data.append(["Closure Rate", "-"])
    # R&D Assist Rate
    if len(close_cases_m) != 0:
        summary_data.append(["R&D Assist Rate", str(round(len(close_cases_m[close_cases_m["R&D Incident"].notna()]) / len(close_cases_m) * 100, 2)) + "%"])
    else:
        summary_data.append(["R&D Assist Rate", "-"])
    # Backlog
    summary_data.append(["Backlog", len(backlog) + len(backlog_history)])
    # Backlog 相关百分比的计算
    # 必须是当月才会计算, 并且 backlog 的值要求大于 0
    if month_offset == 0 and (len(backlog) + len(backlog_history)) >= 0:
        # Backlog > 30 的比例
        try:
            backlog30_percentage = str(round(len(backlog[backlog["Age (Days)"] >= 30.0]) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        except KeyError:
            backlog30_percentage = str(round(len(backlog[backlog["Age"] >= 30.0]) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        summary_data.append(["Backlog > 30", backlog30_percentage])
        # Backlog > 30 并且没有升级的比例
        try:
            backlog30_no_cpe = backlog[backlog["Age (Days)"] >= 30.0]
            backlog30_no_cpe = backlog30_no_cpe[backlog30_no_cpe["R&D Incident"].isna()]
        except KeyError:
            backlog30_no_cpe = backlog[backlog["Age"] >= 30.0]
            backlog30_no_cpe = backlog30_no_cpe[backlog30_no_cpe["R&D Incident"].isna()]
        backlog_30_no_cpe = str(round(len(backlog30_no_cpe) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        summary_data.append(["Backlog > 30 (Support)", backlog_30_no_cpe])
        # Backlog > 90 的比例
        try:
            backlog90_percentage = str(round(len(backlog[backlog["Age (Days)"] >= 90.0]) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        except KeyError:
            backlog90_percentage = str(round(len(backlog[backlog["Age"] >= 90.0]) / (len(backlog) + len(backlog_history)) * 100, 2)) + "%"
        summary_data.append(["Backlog > 90", backlog90_percentage])
        # DTR 计算
        ssdata1 = backlog[backlog["Suggested_Solution_Date"].notna()]
        ssdata2 = close_cases_m[close_cases_m["Suggested_Solution_Date"].notna()]
        ssdata = pd.concat([ssdata1, ssdata2])
        ssdata = ssdata.sort_values(by=["Suggested_Solution_Date"], ascending=False)
        ssdata = ssdata.drop_duplicates(subset="Case Number")
        if len(ssdata) != 0:
            dtrdata = pd.DataFrame()
            dtrdata["Date/Time Opened"] = pd.to_datetime(ssdata["Date/Time Opened"]).dt.date
            dtrdata["Suggested_Solution_Date"] = pd.to_datetime(ssdata["Suggested_Solution_Date"]).dt.date
            dtr = dtrdata["Suggested_Solution_Date"] - dtrdata["Date/Time Opened"]
            dtr_avg = str(round(dtr.sum().days / len(ssdata), 2))
            summary_data.append(["DTR", dtr_avg])
        else:
            summary_data.append(["DTR", "-"])
        # DTR only Support
        ssdata1_os = backlog[backlog["Suggested_Solution_Date"].notna()]
        ssdata2_os = close_cases_m[close_cases_m["Suggested_Solution_Date"].notna()]
        ssdata_os = pd.concat([ssdata1_os, ssdata2_os])
        ssdata_os = ssdata_os.sort_values(by=["Suggested_Solution_Date"], ascending=False)
        ssdata_os = ssdata_os.drop_duplicates(subset="Case ID")
        ssdata_os = ssdata_os[ssdata_os["R&D Incident"].isna()]
        if len(ssdata_os) != 0:
            dtrdata_os = pd.DataFrame()
            dtrdata_os["Date/Time Opened"] = pd.to_datetime(ssdata_os["Date/Time Opened"]).dt.date
            dtrdata_os["Suggested_Solution_Date"] = pd.to_datetime(ssdata_os["Suggested_Solution_Date"]).dt.date
            dtr_os = dtrdata_os["Suggested_Solution_Date"] - dtrdata_os["Date/Time Opened"]
            dtr_os_avg = str(round(dtr_os.sum().days / len(ssdata_os), 2))
            summary_data.append(["DTR Support only", dtr_os_avg])
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

# 分析 Survey Report
if report_survy is not None:
    rawsurv = pd.read_csv(report_survy)
    # 数据预处理
    rawsurv["Customer Feed Back Survey: Last Modified Date"] = pd.to_datetime(rawsurv["Customer Feed Back Survey: Last Modified Date"], format="%Y-%m-%d")
    rawsurv["Closed Data"] = pd.to_datetime(rawsurv["Closed Data"], format="%Y-%m-%d")
    rawsurv = rawsurv.sort_values(by=["Customer Feed Back Survey: Last Modified Date", ], ascending=False)
    rawsurv = rawsurv.drop_duplicates(subset="Case Number")
    # 根据年份和月份筛选数据
    survey_y = rawsurv[rawsurv["Closed Data"].dt.year == y_offset]
    survey_m = survey_y[survey_y["Closed Data"].dt.month == m_offset]
    survey_ces = survey_m[survey_m["OpenText made it easy to handle my case"] >= 8.0]
    survey_cast = survey_m[survey_m["Satisfied with support experience"] >= 8.0]
    # Survey CES & Survey CAST
    if len(survey_m) > 0:
        summary_data.append(["Survey CES", str(round(len(survey_ces) / len(survey_m) * 100, 2)) + "%"])
        summary_data.append(["Survey CAST", str(round(len(survey_cast) / len(survey_m) * 100, 2)) + "%"])
    else:
        summary_data.append(["Survey CES", "-"])
        summary_data.append(["Survey CAST", "-"])
    # SRR (Survey Response Rate)
    if len(survey_m) > 0 and clos_cases_by_month is not None:
        summary_data.append(["Survey Response Rate", str(round(len(survey_m) / len(clos_cases_by_month) * 100, 2)) + "%"])
    else:
        summary_data.append(["Survey Response Rate", "-"])

# 将结果写入到文件中
output_file = "{}-{}".format(str(y_offset), str(m_offset)) + ".csv"
df = pd.DataFrame(summary_data, columns=summary_data[0])
df.to_csv(output_file, index=False, header=["KPI", "{}-{}".format(str(y_offset), str(m_offset))])

# 打印结果
table.add_rows(summary_data)
print(table)
