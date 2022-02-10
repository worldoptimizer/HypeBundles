#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# 	hypebundle.py
#	Helper classes and function for bundles
#
#	 v1.0.0 Initial release
#
#
#	MIT License
#	Copyright (c) 2021 Max Ziebell
#

import sys
import os
import json
import hashlib
import httplib, urllib
import traceback
		

# closure warnings and error helper
def format_closure_feedback(list_of_items, offset=0):
	js_feedback = ''
	for e in list_of_items:
		line_nr = e["lineno"] + offset
		js_feedback += "{} : {} at line {} character {}\n\n".format(e["type"], e.get("error", e.get("warning")), line_nr, e["charno"])
		line = e["line"].decode('string_escape')
		js_feedback += line+"\n "
		line = e["line"].replace("\t"," "*3)
		leading = len(line)-len(string.lstrip(line))
		js_feedback += " "*(leading+e["charno"]-1)+"^"+"\n"
	return js_feedback

# closure API
def compile_with_closure(js_code, cache_folder):
	# prep
	js_warnings = ''
	js_errors = ''

	# check if we compile the code already and return it
	# TBD maybe a folder with 3 files instead of 3 files
	code_cache_file_md5 = os.path.join(cache_folder, hashlib.md5(js_code).hexdigest())
	
	# read warnings
	if os.path.isfile(code_cache_file_md5+'.warn'):
		js_warnings = read_content(code_cache_file_md5+'.warn')
		
	# if we got an error code wasn't generated so return bad code and error
	if os.path.isfile(code_cache_file_md5+'.error'):
		js_errors = read_content(code_cache_file_md5+'.error')
		return js_code, js_errors, js_warnings
	
	#if we got code return cached code and optional warning
	if os.path.isfile(code_cache_file_md5+'.js'):
		js_code = read_content(code_cache_file_md5+'.js')
		return js_code, js_errors, js_warnings

	# TODO add statistics
	# TBD check if we can use code_url to bundle runtime from CDN (full, min)

	# prepare paramters
	params = urllib.urlencode([
		('js_code', js_code),
		('compilation_level', 'SIMPLE_OPTIMIZATIONS'),
		('output_format', 'json'),
		('output_info', 'compiled_code'),
		('output_info', 'warnings'),
		('output_info', 'errors'),
	])

	# send to API
	headers = { "Content-type": "application/x-www-form-urlencoded" }
	
	# let us try to request a compiler API session
	try:
		conn = httplib.HTTPSConnection('closure-compiler.appspot.com')
		conn.request('POST', '/compile', params, headers)
		response = conn.getresponse()
		data = json.loads(response.read().decode('utf-8'))
		conn.close()
		
		# TODO make warnings a list (countable) and return closure maybe a dict
		if "warnings" in data and data["warnings"]!="":
			js_warnings = format_closure_feedback(data["warnings"], len(data.get("errors",[]))*4+4)
			save_content(code_cache_file_md5+'.warn', js_warnings)

		# ckeck if we got the code
		if "compiledCode" in data and data["compiledCode"]!="":

			# cache compiled code using hashlib 
			save_content(code_cache_file_md5+'.js', data["compiledCode"])

			# return
			return data["compiledCode"], js_errors, js_warnings
		else:
			# compiler error 
			if "errors" in data:
				js_errors += format_closure_feedback(data["errors"], len(data["errors"])*4+4)
				save_content(code_cache_file_md5+'.error', js_errors)

				# append it to the return and code
				temp = "/* Closure Compiler\n\n"
				temp += js_errors
				temp += "*/\n"
				js_code =temp+"\n" + js_code

		# retun orginal code to keep running
		return js_code, js_errors, js_warnings
	except Exception as e:
		js_errors = traceback.format_exc()
		js_code = '/* ' + js_errors + '\n\n*/\n' + js_code

		# retun orginal code to keep running
		return js_code, js_errors, js_warnings


def read_content(filepath):
	with open(filepath, "r") as f:
		return f.read()

def save_content(filepath, content):
	with open(filepath, "w") as f:
		f.write(content)
		#f.write(content.encode('utf-8'))