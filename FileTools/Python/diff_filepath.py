#!/usr/bin/python3
# -*- coding: UTF-8 -*-

########################################################################################################################
#   author: zhanghong.personal@outlook.com
#  version: 1.1
#    usage:
#    - create comparedb: diff_filepath.py -d <file/folder path>  -o <database name> [-filter <Regular Exp>] [-not-filter <Regular Exp>] [-debug True]
#    - compare filepath: diff_filepath.py -d <file/folder path> -db <database file> [-filter <Regular Exp>] [-not-filter <Regular Exp>] [-debug True]
# describe: Find different files path in a specified folder
#
# release nodes:
#   2022.02.05 - first release
#   2022.02.06 - Add the -d/-debug args, fix some bugs
########################################################################################################################

import os
import re
import sys
import pickle
import hashlib


def check_args(input_args):
    """
    检查输入的参数, 并返回需要执行的分支所对于的值
    :param input_args:
    :return: dict, values: compare_dict / create_dict / help_dict
    """
    args_db = "Null"
    args_filter = ".*"
    args_not_filter = None
    args_output = "Null"
    args_dst_folder = "Null"
    args_debug = False

    if len(input_args) <= 1:
        return {"mode": "help"}
    else:
        for args in input_args:
            if args in ["-h", "help"]:
                return {"mode": "help"}
            elif args == "-d":
                try:
                    args_dst_folder = input_args[input_args.index("-d") + 1]
                except:
                    return {"mode": "help"}
            elif args == "-db":
                try:
                    args_db = input_args[input_args.index("-db") + 1]
                except:
                    return {"mode": "help"}
            elif args == "-o":
                try:
                    args_output = input_args[input_args.index("-o") + 1]
                except:
                    return {"mode": "help"}
            elif args == "-filter":
                try:
                    args_filter = input_args[input_args.index("-filter") + 1]
                except:
                    return {"mode": "help"}
            elif args == "-debug":
                try:
                    args_debug = input_args[input_args.index("-debug") + 1]
                except:
                    return {"mode": "help"}
            elif args == "-not-filter":
                try:
                    args_not_filter = input_args[input_args.index("-not-filter") + 1]
                except:
                    return {"mode": "help"}

    # 指定了 -db 参数, 说明是比对模式
    if args_dst_folder != "Null" and args_db != "Null":
        return {"mode": "compare",
                "args_dst_folder": args_dst_folder,
                "args_db": args_db,
                "args_filter": args_filter,
                "args_not_filter": args_not_filter,
                "args_debug": args_debug}
    # 指定了 -o 参数, 说明是写入模式
    elif args_dst_folder != "Null" and args_output != "Null":
        return {"mode": "create",
                "args_dst_folder": args_dst_folder,
                "args_output": args_output,
                "args_filter": args_filter,
                "args_not_filter": args_not_filter,
                "args_debug": args_debug}
    # 其余情况
    else:
        return {"mode": "help"}


def file_hash(file_path):
    """
    读取文件并返回文件的 SHA1 值
    :param file_path:
    :return:
    """
    h = hashlib.sha1()
    with open(file_path, 'rb') as f:
        data = f.read()
        h.update(data)
    return h.hexdigest()


def create_diff_db(args_dict):
    """
    读取指定文件夹, 并将文件所对于的 SHA1 保存为字典, 并进行序列化保存
    :param args_dict:
    :return:
    """
    dst_folder = args_dict.get("args_dst_folder")
    filter = args_dict.get("args_filter")
    not_filter = args_dict.get("args_not_filter")
    dbname = args_dict.get("args_output")
    debug = args_dict.get("args_debug")
    debug_value = debug in ["true", "True"]
    diffdb = {}

    if not_filter != None:
        for root, dirs, files in os.walk(dst_folder):
            for file in files:
                filepath = os.path.abspath(os.path.join(root, file))
                if re.findall(not_filter, filepath, re.IGNORECASE) == [] and re.findall(filter, filepath, re.IGNORECASE):
                    try:
                        filehash = file_hash(filepath)
                        diffdb[filepath] = filehash
                        if debug_value:
                            print("[DEBUG] {} | {}".format(filehash, filepath))
                    except Exception as e:
                        print("[WARN] Can't calculate file hash\n-> File is: {}\n-> Reason is: {}".format(filehash, e))
    else:
        for root, dirs, files in os.walk(dst_folder):
            for file in files:
                filepath = os.path.abspath(os.path.join(root, file))
                if re.findall(filter, filepath, re.IGNORECASE):
                    try:
                        filehash = file_hash(filepath)
                        diffdb[filepath] = filehash
                        if debug_value:
                            print("[DEBUG] {} | {}".format(filehash, filepath))
                    except Exception as e:
                        print("[WARN] Can't calculate file hash\n-> File is: {}\n-> Reason is: {}".format(filehash, e))

    with open(dbname, "wb") as f:
        try:
            pickle.dump(diffdb, f)
            print("[INFO] diff db write finish, save path is: {}".format(os.path.abspath(dbname)))
        except Exception as e:
            print("[ERROR] Can't write hash database, reason is: {}".format(e))


def compare_diff_file(args_dict):
    """
    读取指定文件夹, 并指出和记录中不相同的文件
    :param args_dict:
    :return:
    """
    dst_folder = args_dict.get("args_dst_folder")
    filter = args_dict.get("args_filter")
    not_filter = args_dict.get("args_not_filter")
    debug = args_dict.get("args_debug")
    debug_value = debug in ["true", "True"]
    with open(args_dict.get("args_db"), 'rb') as f:
        diffdb = pickle.load(f)

    diff_count = 0

    if not_filter != None:
        for root, dirs, files in os.walk(dst_folder):
            for file in files:
                filepath = os.path.abspath(os.path.join(root, file))
                if re.findall(not_filter, filepath, re.IGNORECASE) == [] and re.findall(filter, filepath, re.IGNORECASE):
                    try:
                        filehash = file_hash(filepath)
                        if filehash != diffdb.get(filepath):
                            print("[DIFF]: {} | {} | {}".format(filehash, diffdb.get(filepath), filepath))
                            diff_count += 1
                            if debug_value:
                                print("[DEBUG] {} | {}".format(filehash, filepath))
                    except Exception as e:
                        print("[WARN] Can't calculate file hash\n-> File is: {}\n-> Reason is: {}".format(filehash, e))
    else:
        for root, dirs, files in os.walk(dst_folder):
            for file in files:
                filepath = os.path.abspath(os.path.join(root, file))
                if re.findall(filter, filepath, re.IGNORECASE):
                    try:
                        filehash = file_hash(filepath)
                        if filehash != diffdb.get(filepath):
                            print("[DIFF]: {} | {} | {}".format(filehash, diffdb.get(filepath), filepath))
                            diff_count += 1
                        if debug_value:
                            print("[DEBUG] {} | {}".format(filehash, filepath))
                    except Exception as e:
                        print("[WARN] Can't calculate file hash\n-> File is: {}\n-> Reason is: {}".format(filehash, e))

    if diff_count == 0:
        print("[INFO] Comparison completed, no different files found.")
    else:
        print("[INFO] Total of {} different files were found!".format(str(diff_count)))


if __name__ == "__main__":
    input_args = sys.argv
    checked = check_args(input_args)
    try:
        if checked.get("mode") == "help":
            print(
                "\n",
                "Usage:\n",
                "1. Generate a filepath hash database on the src path\n",
                "   diff_filepath.py <file/folder path>  -o <database name> [-filter <Regular Exp>] [-not-filter <Regular Exp>] [-debug True]\n",
                "\n",
                "2. Matching dst path using a hash database\n",
                "   diff_filepath.py <file/folder path> -db <database file> [-filter <Regular Exp>] [-not-filter <Regular Exp>] [-debug True]\n",
                "\n",
                "args:\n",
                "# -d            Folder that require hash calculation\n",
                "# -o            Create a hash database\n",
                "# -db           Use hash database to compare file differences\n",
                "# -filter       Regular Exp String, matched path will be calculated hash\n",
                "# -not-filter   Regular Exp String, matched path will not be calculated hash\n",
                "# -debug        If the value is True, it shows which files were read\n",)
        elif checked.get("mode") == "compare":
            compare_diff_file(checked)
        elif checked.get("mode") == "create":
            create_diff_db(checked)
    except Exception as e:
        print("[ERROR] Execution error, reason is: {e}")
