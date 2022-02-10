#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#	Sample Bundle.hype-export
# 
#	Just to test and show all the insert points
#	and data feedbacks in action
#
#	MIT License
#	Copyright (c) 2021 Max Ziebell
#

import json
import sys
import os

# main
def main():
	# prepare bundle instance
	bundle = HypeBundle(
		{
			"current_script_version"		: 1,
			"version_info_url" 				: "https://hypebundles.de/Version/LogicAndExpressions.php", # only returns a version number
			"download_url" 					: "https://hypebundles.de/Bundle/LogicAndExpressions/", # gives a user info to download and install
		}
	)

	# reset log
	#bundle.log('Running '+bundle.folder_name, True)

	# register document arguments
	bundle.register_document_arguments([
		{
			"label" : "One Options",
		},
		{
			"indent" : 1, # adds an indent with ╰
			"label" : "first option",
			"variable" : "hello", #optional
			"default" : "I am default",
		},
		{
			"label" : "More Options",
			"variable" : "more", #optional
		},
		{
			"indent" : 1, # adds an indent with ╰
			"label" : "second option",
			"variable" : "world", #optional
		},
		{
			"indent" : 2,
			"label" : "third option",
			"variable" : "_ff", #optional
		},
	])

	# register extra actions
	bundle.register_extra_actions([
		{
			"label" : "Hello World",
			"function" : "hypeDocument.helloWorld", 
			"arguments":[
				{"label":"Your text", "type": "String"},
			]
		}
	])

	if bundle.args.get_options:

		bundle.exit_with_result({
			"document_arguments" : bundle.get_document_arguments(),
			"extra_actions" : bundle.get_extra_actions(),
			"save_options" : bundle.get_save_options(),
			"min_hype_build_version" : "734", # Hype 4 release with working all_document_arguments_by_export_script
			# "max_hype_build_version" : "798" # uncomment to exclude from Hype 5 (Beta and beyond)
		})


	if bundle.args.get_inserts:

		bundle.set_variable("abra", "kadabra")
		bundle.set_variable("_peter", "I am invisible because I am private")
		bundle.set_variable("peter", "I am invisible because I am private")
	
		# tests	
		bundle.log ( bundle.get_document_argument_value_by_label('second option') )
		bundle.log ( bundle.get_document_argument_value_by_variable('hello') )
		bundle.log ( bundle.get_document_argument_value_by_index(4) )
		
		bundle.log ( json.dumps(bundle.get_all_variables()) )
		bundle.log ( json.dumps(bundle.document_arguments) )

		bundle.log ( 'world = ' + bundle.get_variable('world') )


		bundle.log ( bundle.template_variables("""
		what hello world ${hello} ${world} und ${abra} ${_peter} and ${_ff}
		${peter}
		"""))

		insert_at_head_start = """
		<!-- inserted at head start -->
		"""

		insert_at_head_end = """
		<!-- inserted at head end -->
		"""

		insert_at_body_start = """
		<!-- inserted at body start -->
		"""
		
		insert_at_body_end = """
		<!-- inserted at body end -->
		"""
		
		insert_into_hype_document_load = """
		/** 
		* JavaScript for Sample extension
		*/

		hypeDocument.helloWorld = function (text) {
			alert(text);
		}
		"""

		insert_into_generated_script = '''
		/* some example code to insert in generated script */
		console.log('Hello World from insert_into_generated_script');
		'''

		# collect the options and return them
		bundle.exit_with_result({ 
			'insert_at_head_start' : insert_at_head_start,
			'insert_at_head_end' : insert_at_head_end,
			'insert_at_body_start' : insert_at_body_start,
			'insert_at_body_end' : insert_at_body_end,
			'insert_into_hype_document_load' : insert_into_hype_document_load,
			'insert_into_generated_script' : insert_into_generated_script,
		})

# run main
if __name__ == "__main__":

	# append bundle import path to sys path and mount HypeBundle class
	import_path = 'com.tumult.Hype4/ManagerExtension.bundle/import/'
	sys.path.append(os.path.join(__file__.split('com.tumult.Hype4', 1)[0], import_path))
	from hypebundle import *
	
	# ready so run main
	main()
