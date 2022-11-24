#!/usr/bin/env python3
# python ./wsgi.py
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
import pickle
import glob
from shutil import copyfile
from bs4 import BeautifulSoup
from pandas import DataFrame
import csv


input_file = sys.argv[1]
BASE_URL = sys.argv[2]

def main():
    file_directory(input_file)
    this_pickle(-1)
    setup_files()
    print_log("Using " + BASE_URL, "warning")
    check_codes()
    html_retrieve(input_file)
    html_to_yml()
    this_pickle(len(course_codes))
    print_log("Process complete! Ready to Download", "success")

def file_directory(file):
    """set up input file information"""
    this_file = Path(file)
    global basename, directory, extension
    basename = str(this_file.stem)
    directory = str(this_file.parent)
    extension = str(this_file.suffix)
    print(directory)

def setup_files():
    global cfg, out, session_log, error_log
    cfg = load_yml("./includes/yml/replace.yml")
    out = directory + "/out.html"
    session_log = directory + "/tmp/session_log.txt"
    error_log = directory + "/tmp/error_log.txt"
    mkfile(out)
    mkfile(session_log)
    mkfile(error_log)

def check_codes():
    fread = open(input_file)
    global course_codes
    course_codes=[]
    for line in fread:
        line = line.rstrip()
        course_codes.append(line.rstrip())
    print(course_codes)
    count_course_codes = len(course_codes)
    print(count_course_codes)
    if count_course_codes == 0:
        print_log("Found " + str(count_course_codes) + " courses. Please try another file.", "danger")
    else:
        print_log("Found " + str(count_course_codes) + " courses", "success")

def html_retrieve(file):
    print_log("Collecting HTML pages..", "warning")
    codes = open(file)
    for code in codes:
        this_code = code.rstrip()
        this_html = directory + "/html" + this_code + ".html"
        print(this_html)
        html_exists = os.path.isfile(this_html)
        if html_exists:
            print_log(this_code + " already exists..", "success")
        else:
            url = BASE_URL + this_code
            print(url)
            response = urllib.request.urlopen(url)
            response_url = response.geturl()
            content = response.read()
            html_write(this_html, content)
            if url == response_url:
                print_log(this_code + " retrieved...OK", "success")
                copy_sub_text(this_html)
            else:
                print_log("ERROR! " + this_code + " was not retrieved. Check the input file.", "danger")
                with open(error_log, "a"):
                    print(this_code, " error")

def html_write(file, content):
    with open(file, "wb") as html_write:
        html_write.write(content)
        html_write.close

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

def remove_newlines(file):
    print_log("Processing text files..", "warning")
    clean = open(file).read().replace('\n', '')
    with open(file, 'w') as file_write:
        file_write.write(clean)
        file_write.close

def process_regex(in_file):
    print_log("Cleaning up text files..", "warning")
    this_regex = cfg['regex']
    for key, val in this_regex.items():
        with fileinput.FileInput(in_file, inplace=True) as file:
            for line in file:
                this_sub = re.sub(r"" + key + "", r"" + val + "", line.rstrip())
                print(this_sub)

def pandoc_html():
    print_log("Converting to output format..", "warning")
    try:
        print_log("Creating output file", "warning")
        subprocess.call("pandoc -s " + directory + "/out.html -o" + directory + "/out.docx", shell=True)
    except Exception:
        print("Unable to create feedback file", "danger")

def html_to_yml():
    print(directory)
    out_courses = directory + "/courses.csv"
    out_learning_outcomes = directory + "/learning-outcomes.csv"
    out_assessment = directory + "/assessment.csv"
    out_dict = []
    for filename in sorted(glob.glob(directory + "/html/2023/course/*.html")):
        this_file = Path(filename)
        print(this_file)
        this_basename = str(this_file.stem)
        out_yml = directory + "/yml/" + this_basename + ".yml"
        dict = {}
        with open(filename, 'r') as f:
            contents = f.read()
            soup = BeautifulSoup(contents, 'lxml')

            # course level
            course_meta('course-name', soup, dict)
            course_meta('course-code', soup, dict)
            course_meta('course-year', soup, dict)

            try:
                summary_codes_id = soup.find(class_="degree-summary__codes")
                clean_codes(summary_codes_id, dict)
            except:
                break

            course_text('introduction', soup, dict)
            course_text('requisite', soup, dict)
            course_list('learning-outcomes', soup, dict)
            course_list('indicative-assessment', soup, dict)

        print(dict)
        out_dict.append(dict)

        f = open(out_yml, 'w+')
        yaml.dump(dict, f, allow_unicode=True)

    field_names = ['course-code',
                   'course-name',
                   'course-year',
                   'Offered by',
                   'Course subject',
                   'Areas of interest',
                   'Academic career',
                   'Course convener',
                   'introduction',
                   'requisite',
                   ]

    

    'learning-outcomes',
    'indicative-assessment',

    convert_csv(dict, out_courses, field_names)


def convert_csv(dict, out_file, field_names):
    with open(out_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(dict)

## helper functions

def course_meta(key, text, dict):
    if key:
        try:
            val = text.find('meta', {'name': key}).get('content')
            dict.update({key: val})
        except:
            dict.update({key: ""})

def course_text(key, text, dict):
    if key:
        try:
            html = text.find("div", {"id": key})
            this_text = html.text
            lines = (line.strip() for line in this_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            val = '\n'.join(chunk for chunk in chunks if chunk)
            dict.update({key: val})
        except:
            dict.update({key: ""})

def course_list(key, text, dict):
    count = 1
    this_dict = {}
    if key:
        try:
            html = text.find("h2", {"id": key})
            list = html.find_next("ol")
            for item in list.find_all("li"):
                list = str(count)
                val = str(item.text)
                this_dict.update({list: val})
                count += 1
        except:
            this_dict.update({"list": "None"})

        dict.update({key: this_dict})


def clean_codes(string, dict):
    if string:
        try:
            text = string.findAll('li')
            for li in text:
                key = li.find('span', {'class':'degree-summary__code-heading'})
                val = li.find('span', {'class':'degree-summary__code-text'})
                dict.update({key.text: val.text})
        except:
            dict.update({"": ""})
        return out

def this_pickle(count):
    settings = {"exit": count}
    print(directory)
    pickle.dump(settings, open(directory + "/tmp/settings.txt", "wb"))

def load_yml(file):
    '''Read in a YAML file'''
    with open(file, 'r') as stream:
        c = yaml.safe_load(stream)
    return c

def print_log(message, css):
    with open(directory + "/tmp/" + "session_log.txt", "a") as out:
        out.write("<li class=\"text-" + css + "\">" + message + "</li>")
    print(message)

def mkfile(file):
    f = open(file, "w+")
    f.close

if __name__ == "__main__":
    main()