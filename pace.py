#!/usr/bin/env python3
# python ./pace.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

"""grabs course descriptions on P&C and converts them into a document"""

import urllib.request, urllib.parse
import sys
import os
from pathlib import Path
import yaml
import fileinput
import re
import subprocess
import shutil
import pickle

input_file = sys.argv[1]
BASE_URL = sys.argv[2]


def process_regex(in_file):
    print_log("Cleaning up text files..", "info")
    this_regex = cfg['regex']
    for key, val in this_regex.items():
        with fileinput.FileInput(in_file, inplace=True) as file:
            for line in file:
                this_sub = re.sub(r"" + key + "", r"" + val + "", line.rstrip())
                print(this_sub)

def load_yml(file):
    '''Read in a YAML file'''
    with open(file, 'r') as stream:
        c = yaml.safe_load(stream)
    return c

def print_log(message, css):
    with open(directory + "/tmp/" + "session_log.txt", "a") as out:
        out.write("<li class=\"text-" + css + "\">" + message + "</li>")
    print(message)

def pandoc_html():
    print_log("Converting to output format..", "info")
    try:
        print_log("Creating output file", "success")
        subprocess.call("pandoc -s " + directory + "/out.html -o" + directory + "/out.docx", shell=True)
    except Exception:
        print("Unable to create feedback file", "danger")

def mkfile(file):
    f = open(file, "w+")
    f.close

def remove_newlines(file):
    print_log("Processing text files..", "info")
    clean = open(file).read().replace('\n', '')
    with open(file, 'w') as file_write:
        file_write.write(clean)
        file_write.close

def copy_sub_text(file_in):
    with open(out, "a") as txt_write:
        with open(file_in, "r") as html_read:
            toggle_out = False
            for line in html_read:
                rule_start = [re.match(r".*secondary-navigation-wrapper", line)]
                rule_end = [re.match(r".*<!-- END SUB PLANS -->", line)]
                if any(rule_start):
                    toggle_out = True
                if any(rule_end):
                    toggle_out = False
                if toggle_out:
                    txt_write.write(line)
    txt_write.close

def html_write(file, content):
    with open(file, "wb") as html_write:
        html_write.write(content)
        html_write.close

def html_retrieve(file):
    print_log("Collecting HTML pages..", "info")
    codes = open(file)
    for code in codes:
        this_code = code.rstrip()
        this_html = directory + "/html/" + this_code + ".html"
        html_exists = os.path.isfile(this_html)
        if not html_exists:
            print_log(this_code + "  ", "white")
            url = BASE_URL + this_code
            response = urllib.request.urlopen(url)
            content = response.read()
            html_write(this_html, content)
        copy_sub_text(this_html)

def this_pickle(count):
    settings = {"exit": count}
    print(directory)
    pickle.dump(settings, open(directory + "/tmp/settings.txt", "wb"))

def file_directory(file):
    """set up input file information"""
    this_file = Path(file)
    global basename, directory, extension
    basename = str(this_file.stem)
    directory = str(this_file.parent)
    extension = str(this_file.suffix)

def setup_files():
    # shutil.rmtree('/job/', ignore_errors=True)
    # shutil.rmtree('/download/', ignore_errors=True)
    # os.makedirs('/job/html/')
    # os.makedirs('/job/txt/')
    # os.makedirs('/job/tmp/')
    global cfg, out, session_log
    cfg = load_yml("./includes/yml/replace.yml")
    out = directory + "/out.html"
    session_log = directory + "/tmp/session_log.txt"
    mkfile(out)
    mkfile(session_log)

def check_codes(file):
    fread = open(input_file)
    global course_codes
    course_codes=[]
    for line in fread:
        line = line.rstrip()
        # rules = [re.match(r"^..../d", line)]
        # if any(rules):
        course_codes.append(line.rstrip())
    count_course_codes = len(course_codes)
    print(count_course_codes)
    if count_course_codes == 0:
        print_log("Found " + str(count_course_codes) + " courses. Please try another file.", "danger")
    else:
        print_log("Found " + str(count_course_codes) + " courses", "success")


def main():
    file_directory(input_file)
    this_pickle(-1)
    setup_files()
    print_log("Using " + BASE_URL, "success")
    check_codes(input_file)
    html_retrieve(input_file)
    remove_newlines(out)
    process_regex(out)
    pandoc_html()
    this_pickle(len(course_codes))
    print_log("Process complete! Ready to Download", "success")

if __name__ == "__main__":
    main()