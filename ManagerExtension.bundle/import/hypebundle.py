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
import argparse
import json
import re
import io
import distutils.util



class HypeBaseBundle:
	# store user variables
	_variable_lookup = {}

	# store registerd values
	_extra_actions = {}
	_save_options = {}

	# unicode symbol for indentations
	_L = u'\u2570' #╰


	'''
	Constructor and basics
	'''

	def __init__(self, settings={}):
		# store settings for later
		self.settings = settings

		# store file and folder for later use
		# check if a file was given or default to main file
		self.file = self.settings.get('file', sys.modules['__main__'].__file__)
		self.folder = os.path.dirname(self.file)
		
		# check if we are a bundle
		if self.folder.endswith('.bundle'):
			self.file_name = os.path.basename(self.file)
			self.folder_name = os.path.basename(self.folder)
			self.extensions_folder = os.path.join(self.folder.split('com.tumult.Hype4', 1)[0], 'com.tumult.Hype4')
			self.library_folder	= os.path.join(self.extensions_folder, 'AdvancedCapabilities')
			self.bundles_folder	= os.path.join(self.library_folder, 'Bundles')
			self.cache_folder	= os.path.join(self.library_folder, 'Cache')
			self.logs_folder	= os.path.join(self.library_folder, 'Logs')
			self.manager_folder	= os.path.join(self.extensions_folder, 'ManagerExtension.bundle')


	def parse_known_args(self):
		# default parser options for bundles
		parser = argparse.ArgumentParser()
		parser.add_argument('--hype_version')
		parser.add_argument('--hype_build')
		parser.add_argument('--export_uid')

		parser.add_argument('--get_options', action='store_true')

		parser.add_argument('--modify_staging_path')
		parser.add_argument('--destination_path')
		parser.add_argument('--export_info_json_path')
		parser.add_argument('--is_preview', default="False")
		parser.add_argument('--check_for_updates', action='store_true')

		# custom callbacks for HypeBundle
		parser.add_argument('--get_inserts', action='store_true')

		# store reference
		self.args, self.unknown = parser.parse_known_args()

		# make sure is_preview is cast as boolean
		if not isinstance(self.args.is_preview, bool):
			self.args.is_preview = bool(distutils.util.strtobool(self.args.is_preview))


	def log(self, content, truncate=False):
		# try to log in file base on bundle name
		try:
			with open(os.path.join(self.logs_folder, self.folder_name + '.log'), "a") as f:
				if truncate: f.truncate(0) 
				f.writelines([content.encode('utf-8'), "\n"])
			return True
		except Exception:
			return False


	'''
	Templating (for bundle)
	'''

	def template_variables(self, string, additional_lookup={}, remove_private_document_arguments=True):
		# local dict
		lookup = {}
		
		# update with document arguments and user defiend variables
		lookup.update(self.get_all_variables())

		# remove document arguments starting with an underscore 
		if remove_private_document_arguments:
			lookup = { key:value for (key,value) in lookup.items() if key[0:1] != '_'}

		# add ad hoc variables added to the update
		lookup.update(additional_lookup)
		
		# replace variables in string
		return template_variables(string, lookup)

		
	def get_all_variables(self):
		variables = self.document_arguments_variables.copy()
		variables.update(self._variable_lookup)
		return variables


	def get_variable(self, key, default=''):
		value = self.get_all_variables().get(key, default)
		return '' if value == None else value

		
	def set_variable(self, key, value=None):
		self._variable_lookup[key] = value


	def _prepare_document_variables(self):
		# try extracting all variable into class for a static lookup
		# called after registering document arguments when values are expected
		try:
			def check(l): return 'variable' in l
			document_arguments_with_variables = list(filter(check, self.document_arguments_lookup))
			self.document_arguments_variables = {arg['variable'] : self.get_document_argument_value_by_variable(arg['variable']) for arg in document_arguments_with_variables}
		except KeyError:
			self.document_arguments_variables = {}


	'''
	Private Helper
	'''

	def _load_export_info(self):
		# try to load export info based on args.export_info_json_path
		# only works in args.modify_staging_path
		# return success as boolean
		try:
			export_info_file = open(self.args.export_info_json_path)
			self.export_info = json.loads(export_info_file.read())
			export_info_file.close()
			return True
		except Exception:
			return False


	def _prepare_document_arguments(self):
		# try fetching/finding the document arguments based on the bundle name
		try:
			self.document_arguments = self.export_info['all_document_arguments_by_export_script'][self.file_name]
			return True
		except Exception:
			return False
	

	'''
	Exits
	'''

	def exit_with_result(self, result):
		# exit bundle and return options back to Hype
		print "===================="
		print json.dumps({"result" : result})
		sys.exit(0)


	'''
	Document Arguments
	'''

	def register_document_arguments(self, document_arguments_lookup):
		# register document arguments with extra options to offer more capabilities
		# but it be aware that Hype only saves values using the label as index.
		# Hence, unfortunately changing indentation or the label results in loosing the stored values
		self.document_arguments_lookup = document_arguments_lookup
		self.document_arguments_list = [self._indent_document_argument(arg) for arg in document_arguments_lookup]
		if self.args.modify_staging_path:
			self._prepare_document_variables()


	def get_document_arguments(self):
		# try returning the document arguments as a play list of labels
		try:
			return self.document_arguments_list
		except Exception:
			pass


	def get_document_argument_value(self, key, default=''):
		# try returning a document argument value based on the raw lookup key
		# meaning a key that includes indentations and unicode characters
		try:
			return self.document_arguments[key]
		except KeyError:
			return default


	def get_document_argument_value_by_label(self, label, default=''):
		# try returning a document argument value using the registerd label name
		# by filtering the registered arguments and genereating the raw lookup key
		try:
			def check(l): return label == l.get('label')
			arg = list(filter(check, self.document_arguments_lookup))
			if len(arg) > 0:
				key = self._indent_document_argument(arg[0])
				return self.document_arguments[key]
		except KeyError:
			pass
		return default


	def get_document_argument_value_by_variable(self, variable, default=''):
		# try returning a document argument value using the registerd variable name
		# by filtering the registered arguments and genereating the raw lookup key
		try:
			def check(l): return variable == l.get('variable')
			arg = list(filter(check, self.document_arguments_lookup))
			if len(arg) > 0:
				key = self._indent_document_argument(arg[0])
				default = arg[0].get('default')
				value = self.document_arguments.get(key, default)
				return value if value and not value.isspace() else default
		except KeyError:
			pass
		return default


	def get_document_argument_value_by_index(self, index, default=''):
		# try returning a document argument value using the index
		# by returning the value from the given indexed argument in the registered dict
		try:
			if index < len(self.document_arguments_lookup):
				key = self._indent_document_argument(self.document_arguments_lookup[index])
				return self.document_arguments[key]
		except KeyError:
			pass
		return default


	def _indent_document_argument(self, arg):
		# format indentation by modifiying label with spaces and unicode symbol
		if "indent" in arg and arg["indent"] != None:
			return '    '*(arg["indent"]-1) + self._L + ' ' + arg["label"]
		return arg["label"]


	'''
	Extra Actions
	'''	

	def register_extra_actions(self, extra_actions):
		self._extra_actions = extra_actions


	def get_extra_actions(self):
		return self._extra_actions


	'''
	Save Options
	'''	

	def register_save_options(self, save_options):
		self._save_options = save_options


	def get_save_options(self):
		return self._save_options

	'''
	Helper
	'''	


	def is_enabled(self, value):
		try:
			return value.lower() in ['true', 'enabled', 'on', 'yes']
		except Exception:
			return False

	def is_disabled(self, value):
		try:
			return value.lower() in ['false', 'disabled', 'off', 'no']
		except Exception:
			return False


	def variable_is_enabled(self, name):
		try:
			return self.is_enabled(self.get_variable(name))
		except Exception:
			return False

	def variable_is_disabled(self, name):
		try:
			return self.is_disabled(self.get_variable(name))
		except Exception:
			return False

	'''
	Updates
	'''
	def _check_for_updates(self):
		# extract local variables from settings dict with defaults
		defaults_bundle_identifier = self.settings.get('defaults_bundle_identifier', ("de.hypebundles."+self.folder_name).replace(" ", ""))
		minimum_update_check_duration_in_seconds = self.settings.get('minimum_update_check_duration_in_seconds', 10) #60 * 60 * 24)  # once a day
		current_script_version = self.settings.get('current_script_version')
		version_info_url = self.settings.get('version_info_url')
		download_url = self.settings.get('download_url')

		# update logic by Tumult
		import subprocess
		import urllib2
		
		last_check_timestamp = None
		
		try:
			last_check_timestamp = subprocess.check_output(["defaults", "read", defaults_bundle_identifier, "last_check_timestamp"]).strip()
			self.log("checked "+str(last_check_timestamp))
		except:
			pass

		try:
			timestamp_now = subprocess.check_output(["date", "+%s"]).strip()
			self.log("now "+str(timestamp_now))
			if (last_check_timestamp == None) or ((int(timestamp_now) - int(last_check_timestamp)) > minimum_update_check_duration_in_seconds):
				subprocess.check_output(["defaults", "write", defaults_bundle_identifier, "last_check_timestamp", timestamp_now])
				request = urllib2.Request(version_info_url, headers={'User-Agent' : "Magic Browser"})
				latest_script_version = int(urllib2.urlopen(request).read().strip())
				
				if latest_script_version > current_script_version:
					bundle.exit_with_result({
						"url" : download_url, 
						"from_version" : str(current_script_version), 
						"to_version" : str(latest_script_version)
					})
		except:
			pass



class HypeBundle(HypeBaseBundle):

	'''
	Constructor and basics
	'''

	def __init__(self, settings={}):
		
		HypeBaseBundle.__init__(self, settings)

		# parse args given to Python call (mainly subprocess)
		self.parse_known_args()

		# check for updates if possible
		if self.args.check_for_updates:
			self._check_for_updates()
			
		# check if we are installed
		if not self.folder.__contains__(self.bundles_folder):
			# if we are deactivated only return basic save options
			if self.args.get_options:
				self.exit_with_result({
					"save_options" : self.get_save_options(),
				})
			sys.exit(0)


		# prepare based on args
		if self.args.modify_staging_path:
			# hype id	
			self.hype_document_name = os.path.basename(self.args.modify_staging_path)
			# prepare export info and document arguments
			self._load_export_info()
			self._prepare_document_arguments()	


	def get_save_options(self):
		obj = self._save_options.copy()
		obj.update({
			"allows_export" : False,
			"allows_preview" : False,
		})
		return obj



class ManagerExtensionBundle(HypeBaseBundle):

	_NEW	= ' ᴺᴱᵂ'
	_L 		= u'\u2570' #╰
	_LS 	= _L+' '

	'''
	Constructor and basics
	'''
	def __init__(self, settings={}):
		
		HypeBaseBundle.__init__(self, settings)
		
		# parse args given to Python call (mainly subprocess)
		self.parse_known_args()

		# check for updates if possible
		if self.args.check_for_updates:
			self._check_for_updates()

		# check if we are installed
		if not self.folder.__contains__(self.manager_folder):
			# if we are deactivated only return basic save options
			if self.args.get_options:
				self.exit_with_result({
					"save_options" : self.get_save_options(),
				})
			sys.exit(0)
			

		# prepare based on args
		if self.args.modify_staging_path:
			# hype id	
			self.hype_document_name = os.path.basename(self.args.modify_staging_path)
			# prepare export info and document arguments
			self._load_export_info()
			self._prepare_document_arguments()



'''
Render template variables (general)
'''

def template_variables(string, lookup):
	try:
		# filter out variables starting with an underscore
		# lookup = { key:value for (key,value) in loopup.items() if key[0:1] != '_'}

		# build regex pattern for one pass replacement
		varlist = '|'.join([re.escape('${'+key+'}') for key in lookup.keys()])
		pattern = re.compile(r'(' + varlist + r')')
		
		# use lambda to replace with lookup values (removing added var padding 2:-1)
		return pattern.sub(lambda x: lookup[x.group()[2:-1]], string)
	
	except Exception:
		# default to return original string if it fails
		return string

	# TODO: ${ifdef ...}
	# think about using template, tbd: https://stackabuse.com/formatting-strings-with-the-python-template-class/

def read_content(filepath):
	with open(filepath, "r") as f:
		return f.read()

def save_content(filepath, content):
	with open(filepath, "w") as f:
		f.write(content)
		#f.write(content.encode('utf-8'))
