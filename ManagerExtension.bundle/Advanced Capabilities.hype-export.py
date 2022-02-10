#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# 	Advanced Settings and Plugins.hype-export.py
#	Just some helpful additional actions for Tumult Hype
#
#	 v1.0.0 Logic, Queries, Expressions and Variables
#	 v1.0.1 Fixed scope, HypeDocumentLoad in functions()
#	 v1.0.2 limited to id, refactored python, IIFE
#	 v1.0.3 refactored JS, streamline API, replace Eval with new Function
#	 v1.0.4 multi behavior, refactored JS , external functions, closure compiler
#	 v1.0.5 error handling closure compiler, bundle managment, subprocess errors
#	 v1.0.6 name change, bundles, bundle management
#	 v1.0.7 improved cache, added closure warning on preview
#	 v1.0.8 name change, refactored to use HypeBaseBundle
#


import os
import sys
import argparse
import json
import distutils.util
import fnmatch
import string
import shutil
import re
import subprocess
#from subprocess import CalledProcessError

script_version = 'v1.0.9'

#
#	MIT License
#	Copyright (c) 2021 Max Ziebell
#

# main
def main():

	bundle = ManagerExtensionBundle(
		{
			"current_script_version"		: 1, #script_version
			"version_info_url" 				: "https://hypebundles.de/Version/ManagerExtension.php",
			"download_url" 					: "https://hypebundles.de/",
		}
	)

	menu_list = [
		{
			"label" : "Closure Compiler",
		},
		{
			"indent" : 1,
			"label" : "compile on export",
			"variable" : "_closure_compiler_on_export",
			"default" : False,
		},
		{
			"indent" : 1,
			"label" : "compile on preview",
			"variable" : "_closure_compiler_on_preview",
			"default" : False,
		},
		{
			"indent" : 2,
			"label" : "show warnings",
			"variable" : "_closure_compiler_warnings",
			"default" : False,
		},
		{	
			"label" : ""
		},
		{
			"label" : "JavaScript",
		},
		{
			"indent" : 1,
			"label" : "disable error reporting",
			"variable" : "_disable_javascript_errors",
		},
		{	
			"label" : "" 
		},
		{
		"label" : "Installed Bundles⁽¹⁾",
		}
	]

	# TODO get bundles that are by default on or off

	for path, dirs, files in os.walk(bundle.bundles_folder):
		for filename in fnmatch.filter(files, '*.hype-export.py'):
			# make sure all bundles can be run
			filepath = os.path.join(path, filename)
			os.system("chmod 755 '"+filepath+"'")
			# register in overview
			label = filename.replace('.hype-export.py','')
			identifier = '_bundle_'+filename.replace('.hype-export.py','')
			menu_list.append({
				"indent" : 1,
				"label" : label,
				"variable" : identifier,
			})
	

	menu_list.extend([
		{
			"label" : "_______________"*2,
		},
		{
			"label" : "⁽¹⁾Type \"off\" to exclude Bundle",
		}
	])		

	# register document arguments
	bundle.register_document_arguments(menu_list)

	# if we are getting the options
	if bundle.args.get_options:
		bundle.exit_with_result({
			"document_arguments" : bundle.get_document_arguments(),
			"save_options" : bundle.get_save_options(),
			"min_hype_build_version" : "734", # Hype 4 release with working all_document_arguments_by_export_script
			# "max_hype_build_version" : "798" # uncomment to exclude from Hype 5 (Beta and beyond)
		})

	# if we are previewing or exporting
	elif bundle.args.modify_staging_path != None:
		
		# hype id	
		hype_document_name = os.path.basename(bundle.args.modify_staging_path)

		# use acme debugger interface on previews
		acme_debugger = True

		# read and prepare action helper
		global hype_document_load
		global prepend_to_hype_functions
		global subprocess_error

		# results for supported bundle returns
		insert_at_head_start = []
		insert_at_head_end = []
		insert_at_body_start = []
		insert_at_body_end = []
		insert_into_hype_document_load = []
		insert_into_generated_script = []
		patch_generated_script = []

		# arguments for calls
		bundle_args = [
			'--get_inserts', 'True',
			'--modify_staging_path', "'{}'".format(bundle.args.modify_staging_path),
			'--destination_path', "'{}'".format(bundle.args.destination_path),
			'--is_preview', str(bundle.args.is_preview),
			'--export_uid', bundle.args.export_uid,
			'--export_info_json_path', "'{}'".format(bundle.args.export_info_json_path),
			'--hype_version', bundle.args.hype_version,
			'--hype_build', bundle.args.hype_build,
		]

		for path, dirs, files in os.walk(bundle.bundles_folder):
			for filename in fnmatch.filter(files, '*.hype-export.py'):

				# filepath and base filename
				filepath = os.path.join(path, filename)
				identifier = '_bundle_'+filename.replace('.hype-export.py','')

				# check if the user disabled 
				if not bundle.variable_is_disabled(identifier):

					# subprocess
					cmd ="python '"+filepath+"' "+(' '.join(bundle_args))

					# run the subprocess
					try:
						pipe = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

					# and show error to user if it fails
					except CalledProcessError as e:
						pipe = '===================='+json.dumps({
							'result' : {
								'insert_at_body_start' : template_variables(subprocess_error, {
										'subprocess_error': e.output
									})
							}
						})

					# fetch the result
					result = {}
					if (pipe != None):
						data = json.loads(pipe.replace('====================','',1))
						if 'result' in data:
							result = data['result']
					
					if 'insert_at_head_start' in result and is_valid_string(result['insert_at_head_start']):
						insert_at_head_start.append(result['insert_at_head_start'].decode('string_escape'))

					if 'insert_at_head_end' in result and is_valid_string(result['insert_at_head_end']):
						insert_at_head_end.append(result['insert_at_head_end'].decode('string_escape'))

					if 'insert_at_body_start' in result and is_valid_string(result['insert_at_body_start']):
						insert_at_body_start.append(result['insert_at_body_start'].decode('string_escape'))

					if 'insert_at_body_end' in result and is_valid_string(result['insert_at_body_end']):
						insert_at_body_end.append(result['insert_at_body_end'].decode('string_escape'))

					if 'insert_into_hype_document_load' in result and is_valid_string(result['insert_into_hype_document_load']):
						insert_into_hype_document_load.append(result['insert_into_hype_document_load'].decode('string_escape'))

					if 'insert_into_generated_script' in result and is_valid_string(result['insert_into_generated_script']):
						insert_into_generated_script.append(result['insert_into_generated_script'].decode('string_escape'))

					if 'patch_generated_script' in result and is_valid_string(result['patch_generated_script']):
						patch_generated_script.append(result['patch_generated_script'])


		# substitutions for hype_document_load
		hype_document_load = template_variables(hype_document_load, {
				'insert_into_hype_document_load'	:	"\n".join(insert_into_hype_document_load),
				'hype_document_name'				:	hype_document_name,
				'script_version'					:	script_version,
			})

		# substitutions for hype functions header
		prepend_to_hype_functions = template_variables(prepend_to_hype_functions, {
				'hype_document_name'	:	hype_document_name
			})

		# now modifiy generated script
		for path, dirs, files in os.walk(os.path.abspath(bundle.args.modify_staging_path)):
			for filename in fnmatch.filter(files, '*_hype_generated_script.js'):
				
				# filepath and read
				filepath = os.path.join(path, filename)
				generated_script = read_content(filepath)
				
				# replace relative with absolute calls in generated script
				generated_script = generated_script.replace(r'exportScriptOid:".*?\.hype-export\.py",', '')
				generated_script = generated_script.replace('s:"hypeDocument.', 's:"HYPE.documents[\\"'+hype_document_name+'\\"].')
				
				# hype function regex with Friedl's "unrolled loop)
				pattern = re.compile(r'name:"(.*?)",source:"([^"\\]*(?:\\.[^"\\]*)*)"')
				signature = "function(hypeDocument, element, event) {"
				
				# unpack hype functions
				hype_functions = ''
				for m in re.finditer(pattern, generated_script):
					new_name = 'HYPE_functions[\\"'+hype_document_name+'\\"].'+m.group(1)
					generated_script = generated_script.replace(m.group(2), new_name)
					new_name_decoded = new_name.decode('string_escape')
					function_raw = m.group(2).replace(signature, signature+"\n");
					function_decoded = function_raw.decode('string_escape')
					hype_functions = hype_functions+"\n"+new_name_decoded+" = "+function_decoded+";\n"
					hype_functions += '//'+m.group(2)+"\n"
				
				# add javascript for actions and hype functions
				script_additions = prepend_to_hype_functions+"\n"+hype_functions+"\n"+hype_document_load

				# add further addition from the bundles
				if len(insert_into_generated_script):
					script_additions += "\n".join(insert_into_generated_script)					

				# use closure API on exports if enabled
				if not bundle.args.is_preview and bundle.variable_is_enabled('_closure_compiler_on_export'):
					script_additions, js_errors, js_warnings = compile_with_closure(script_additions, os.path.join(bundle.cache_folder, 'Closure'))

				# use closure API on previews if enabled
				if bundle.args.is_preview and bundle.variable_is_enabled('_closure_compiler_on_preview'):
					script_additions, js_errors, js_warnings = compile_with_closure(script_additions, os.path.join(bundle.cache_folder, 'Closure'))
					if js_errors:
						insert_at_body_start.append(template_variables(closure_error, { 'closure_error' : js_errors }))
					if js_warnings and bundle.variable_is_enabled('_closure_compiler_warnings'):
						insert_at_body_start.append(template_variables(closure_warning, { 'closure_warning' :  js_warnings }))

				# append script
				generated_script = script_additions+"\n"+generated_script;

				#save
				save_content(filepath, generated_script)
		
		# pull in debugger resources if enabled and preview
		if acme_debugger and bundle.args.is_preview:
			shutil.copy(os.path.join(bundle.folder, 'acme_debugger.css'), bundle.args.modify_staging_path)
			shutil.copy(os.path.join(bundle.folder, 'acme_debugger.js'), bundle.args.modify_staging_path)
			insert_at_head_end.append('<link rel="stylesheet" href="acme_debugger.css" />')
			insert_at_head_end.append('<script src="acme_debugger.js" type="text/javascript"></script>')
			if not bundle.variable_is_enabled('_disable_javascript_errors'):
				insert_at_head_end.append(javascript_error)


		# load index html template
		index_path = os.path.join(bundle.args.modify_staging_path, bundle.export_info['html_filename'].encode("utf-8"))
		index_contents = read_content(index_path)
		
		# perform accumulated substitutions 
		if len(insert_at_head_start):
			index_contents = insert_at_start("<head.*?>", index_contents, "\n".join(insert_at_head_start))
		
		if len(insert_at_head_end):
			index_contents = insert_at_end("</head", index_contents, "\n".join(insert_at_head_end)) 
		
		if len(insert_at_body_start):
			index_contents = insert_at_start("<body.*?>", index_contents, "\n".join(insert_at_body_start))
		
		if len(insert_at_body_end):
			index_contents = insert_at_end("</body", index_contents, "\n".join(insert_at_body_end))			

		# save results
		save_content(index_path, index_contents)

		# push to final destination
		# TBD introduce export bundles that can take over this step, single plugin set by user
		shutil.rmtree(bundle.args.destination_path, ignore_errors=True)
		shutil.move(bundle.args.modify_staging_path, bundle.args.destination_path)

		# let Hype know that we are done
		bundle.exit_with_result(True)




# functions for conditions to inject in generated script
prepend_to_hype_functions = """/** 
* Hype functions defined for HYPE.documents["${hype_document_name}"]
*/

if("HYPE_functions" in window === false) window.HYPE_functions = Object();
window.HYPE_functions["${hype_document_name}"] = Object();
"""

hype_document_load = """/** 
* Advanced Capabilities Manager Extension (ACME) 
* ${script_version} by Max Ziebell
*/

;(function () {

	/* @const */
	const _standalone = false;

	if("HYPE_eventListeners" in window === false) window.HYPE_eventListeners = Array();
	window.HYPE_eventListeners.push({"type":"HypeDocumentLoad", "callback":function (hypeDocument, element, event) {
		
		if (!_standalone) if (hypeDocument.documentName()!=="${hype_document_name}") return;
	
		${insert_into_hype_document_load}

		/** 
		* JavaScript for Manager Extension
		*/

		// trigger comma seperated list of behaviors
		hypeDocument.triggerCustomBehaviorNamedAll = function(behaviors){
			behaviors.split(',').forEach(function(behavior){
				hypeDocument.triggerCustomBehaviorNamed(behavior.trim());
			});
		}
		
		// Fire HypeDocumentLoad from hypeDocument.functions() if present
		if (hypeDocument.functions()['HypeDocumentLoad']) {
			hypeDocument.functions()['HypeDocumentLoad'](hypeDocument, element, event);
		}

		return true;
	}
	});

})();
"""

subprocess_error= """
<pre style='padding: 40px; margin-top: 0px; background-color:black;color:white; tab-size: 4;'>${subprocess_error}</pre>
"""

closure_warning= """
<script>showClosureCompilerWarning(`${closure_warning}`);</script>
"""

closure_error= """
<script>showClosureCompilerError(`${closure_error}`);</script>
"""

javascript_error= """
<script>window.onerror = showJavaScriptError;</script>
"""


if __name__ == "__main__":

	# log errors to bundle
	sock = open(os.path.dirname(__file__)+'/errors.log', 'a')
	sys.stderr = sock
	
	# append bundle import path to sys path and mount HypeBundle class
	sys.path.append(os.path.join(os.path.dirname(__file__), 'import/'))

	from hypebundle import *
	from closurecompiler import *

	# functions
	def insert_at_start(pattern, string, insert):
		temp = re.search(pattern, string, re.IGNORECASE).end()
		return string[:temp] + insert + string[temp:]

	def insert_at_end(pattern, string, insert):
		temp = re.search(pattern, string, re.IGNORECASE).start()
		return string[:temp] + insert + string[temp:]

	def is_valid_string(value):
		# basestring in 2.7 else str
		return isinstance(value, basestring) and value.strip()

	# ready so run main
	main()
