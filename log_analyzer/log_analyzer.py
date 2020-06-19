#!/usr/bin/env python
# -*- coding: utf-8 -*-

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
# '$status $body_bytes_sent "$http_referer" '
# '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
# '$request_time';

import argparse
import configparser  # импортируем библиотеку
import fnmatch
import gzip
import json
import logging
import os
import re
from operator import itemgetter
from string import Template


def set_logger():
    handlers = []
    log_file = "log_analyzer.log"
    handlers.append(logging.FileHandler(log_file))
    handlers.append(logging.StreamHandler())
    logging_level = logging.INFO
    logging.basicConfig(
        level=logging_level,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        handlers=handlers
    )
    return logging.getLogger('tcpserver')


def set_up():
    parser.add_argument("--config", "-c",
                        help="Configuration file",
                        default="none")
    args = parser.parse_args()
    if args.config == "none":
        return
    if os.path.isfile(args.config):
        try:
            ini.read(args.config)
        except Exception as e:
            logging.error(f'config file parsing error {repr(e)}')
    else:
        logging.error(f'config file {args.config} dose not exists')
        exit(1)
    return


def get_param(param):
    section = "CONFIG"
    if ini.has_option(section, param):
        return ini.get(section, param)
    else:
        return config[param]


def get_date_from_postfix(file_name):
    try:
        return re.search(r"\d{8}", file_name)[0]
    except (IndexError, Exception):
        return ""


def get_file_ext(file_name):
    ext = re.split(r"\.", file_name)[-1]
    if ext.startswith("log-"):
        ext = ""
    return ext


def gen_find(file_part, top):
    for path, dir_list, file_list in os.walk(top):
        for name in filter(lambda x: get_file_ext(x) in ["", "gz"], fnmatch.filter(file_list, file_part)):
            yield os.path.join(path, name)


def get_recent_filename(filenames):
    return max(filenames, key=get_date_from_postfix)


def open_log_file(filename):
    try:
        if filename.endswith(".gz"):
            return gzip.open(filename)
        else:
            return open(filename)
    except OSError:
        logger.error(f"os error ({repr(exc)}) when working with source file ({filename}).")
        return None


def get_url(line):
    search_result = re.search(r'("GET |"POST )(.*?)[" ]', line)
    if search_result:
        return search_result.group(2)[0:128], True
    else:
        return f'parse url error on line: {line}', False


def get_duration(line):
    try:
        return float(re.split(r" ", line)[-1]), True
    except (IndexError, Exception):
        return -1, False


def gen_parser(lines):
    line_counter = 0
    error_counter = 0
    for line in lines:
        line_counter += 1
        url, parsed = get_url(line)
        if not parsed:
            error_counter += 1
        duration, parsed = get_duration(line)
        if not parsed:
            error_counter += 1
        yield url, duration, line_counter, error_counter


def median(lst):
    half = len(lst) // 2
    lst.sort()
    if not len(lst) % 2:
        return (lst[half - 1] + lst[half]) / 2.0
    return lst[half]


def collect_statistics_from_file(filename):
    try:
        with open_log_file(filename) as f:
            return collect_statistics(gen_parser(f.readlines()))
    except OSError:
        logger.error(f"os error ({repr(exc)}) when working with source file ({filename}).")
        return None


def collect_statistics(lines):
    def align(d):
        return round(d, 3)

    urls = dict()
    max_error_percent = float(get_param("MAX_ERROR_PERCENT"))
    line_counter = 0
    error_counter = 0
    for url, duration, line_counter, error_counter in lines:
        if url in urls:
            urls[url].append(duration)
        else:
            urls[url] = [duration]
    if ((error_counter / line_counter) * 100) > max_error_percent:
        logger.error("too many parse errors")
        return
    total_count = 0
    total_time = 0.000
    result_list = list()
    for url, durations in urls.items():
        result_row = dict()
        result_row["url"] = url
        result_row["count"] = count = len(durations)
        result_row["time_sum"] = time_sum = align(sum(durations))
        result_row["time_avg"] = 0 if count == 0 else align(time_sum / count)
        result_row["time_max"] = max(durations)
        result_row["time_med"] = align(median(durations))
        total_time += time_sum
        total_count += count
        result_list.append(result_row)
    for row in result_list:
        row["time_perc"] = align(row["time_sum"] * 100 / total_time)
        row["count_perc"] = align(row["count"] * 100 / total_count)
    return result_list


def squeeze_out(lst, size):
    lst.sort(reverse=True, key=itemgetter("time_sum"))
    lst = lst[:size]
    return lst


def make_report():
    filenames = gen_find(get_param("LOG_FILE_MASK"), get_param("LOG_DIR"))
    recent = get_recent_filename(filenames)
    if os.path.isfile(recent):
        logger.info(f"recent log file: {recent}")
    else:
        logger.info(f"nothing to analyze.")
        return
    date = get_date_from_postfix(recent)
    report_file_name = os.path.join(get_param("REPORT_DIR"), "report-" + date[0:4] + '.' + date[4:6] + '.' + date[6:8] + '.html')
    if os.path.isfile(report_file_name):
        logger.info(f"report {report_file_name} already exists.")
        return
    result_list = collect_statistics_from_file(recent)
    if not result_list:
        logger.error("broken or empty statistic data")
        return
    json_array = json.dumps(squeeze_out(result_list, int(get_param("REPORT_SIZE"))))
    try:
        with open("report.html", "r") as template_file:
            template_string = template_file.read()
            result_string = Template(template_string).safe_substitute(table_json=json_array)
            with open(report_file_name, "w") as report_file:
                report_file.write(result_string)
            logger.info(f"report {report_file_name} created.")
    except OSError as e:
        logger.error(f"os error ({repr(e)}) when working with template file.")


def main():
    app_name = os.path.basename(__file__)
    logger.info(app_name + " started.")
    make_report()
    logger.info(app_name + " finished.")


config = {
    "REPORT_SIZE": 10,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE_MASK": "*nginx-access-ui.log-????????*",
    "MAX_ERROR_PERCENT": 20
}
parser = argparse.ArgumentParser()
ini = configparser.ConfigParser()
logger = set_logger()

if __name__ == "__main__":
    try:
        set_up()
        main()
    except Exception as exc:
        logger.exception(f"exception in main(): {repr(exc)}")
        exit(1)
