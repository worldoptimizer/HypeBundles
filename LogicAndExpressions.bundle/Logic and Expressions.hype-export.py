#!/usr/bin/python

#	Logic and Expressions.extension.hype-export
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
	bundle = HypeBundle()

	# reset log
	bundle.log('Running '+bundle.folder_name, True)

	# register extra actions
	bundle.register_extra_actions([
		{
			"label" : "Conditional Behavior",
			"function" : "hypeDocument.conditionalBehavior", 
			"arguments":[
				{"label":"Expression", "type": "String"},
				{"label":"Behavior true", "type": "String"}, 
				{"label":"Behavior false", "type": "String"}
			]
		},
		{
			"label" : "Set Variable", 
			"function" : "hypeDocument.setVariable",
			"arguments":[
				{"label":"Variable", "type": "String"}, 
				{"label":"Expression", "type": "String"}
			]
		},
		{
			"label" : "Run Function by Selector",
			"function" : "hypeDocument.runFunctionBySelector",
			"arguments":[
				{"label":"Function", "type": "String"},
				{"label":"Selector", "type": "String"}
			]
		},
		{
			"label" : "Run JavaScript Expression",
			"function" : "hypeDocument.runJavaScriptExpression", 
			"arguments":[
				{"label":"Expression", "type": "String"}
			]
		},
	])


	if bundle.args.get_options:

		bundle.exit_with_result({
			"extra_actions" : bundle.get_extra_actions(),
			"save_options" : bundle.get_save_options(),
			"min_hype_build_version" : "734", # Hype 4 release with working all_document_arguments_by_export_script
			# "max_hype_build_version" : "798" # uncomment to exclude from Hype 5 (Beta and beyond)
		})


	if bundle.args.get_inserts:

		insert_into_hype_document_load = """
		/** 
		* JavaScript for Logic extension
		*/

		var validNames = new RegExp('^[a-zA-Z_$][0-9a-zA-Z_$]*$');

		hypeDocument.conditionalBehavior = function (expression, isTrueBehavior, isFalseBehavior) {
			if (!expression || (!isTrueBehavior && !isFalseBehavior)) return;
			var result = this.runJavaScriptExpression(expression, 'Condition Error');
			if (result) {
				if (isTrueBehavior) hypeDocument.triggerCustomBehaviorNamedAll(isTrueBehavior);
			} else {
				if (isFalseBehavior) hypeDocument.triggerCustomBehaviorNamedAll(isFalseBehavior);
			}
		}

		hypeDocument.setVariable = function (variable, expression) {
			if (!variable || !expression) return;
			variable = variable.trim();
			if (!validNames.test(variable)) return;
			if (!hypeDocument.customData[variable]) hypeDocument.customData[variable] = null;
			hypeDocument.customData[variable] = this.runJavaScriptExpression(expression, 'Variable Error');
		}

		hypeDocument.runFunctionBySelector = function (fnc, selector) {
			if (!hypeDocument.functions()[fnc] || !selector) return;
			var sceneElm = document.getElementById(hypeDocument.currentSceneId());
			var elms = sceneElm.querySelectorAll(selector);
			elms.forEach(function(elm){
				hypeDocument.functions()[fnc].call(window, hypeDocument, elm, {type:'runFunctionBySelector'});
			});
		}

		hypeDocument.runJavaScriptExpression = function (expression, errorMsg, omitContext, omitError) {
			if (!expression) return;
			var context='';
			if (!omitContext) for(var variable in hypeDocument.customData) {
				if (validNames.test(variable)) 
					context+='var '+ variable +' = hypeDocument.customData["'+ variable +'"];';
			}
			try {
				return Function('hypeDocument', '"use strict";'+context+'return (' + expression + ')')(hypeDocument);
			} catch (e){
				alert ((errorMsg||'Expression Error')+(!omitError? ': '+e:''));
			}
		}
		"""

		bundle.exit_with_result({
			'insert_into_hype_document_load' : insert_into_hype_document_load,
		})


# run main
if __name__ == "__main__":

	# append bundle import path to sys path and mount HypeBundle class
	import_path = 'com.tumult.Hype4/ManagerExtension.bundle/import/'
	sys.path.append(os.path.join(__file__.split('com.tumult.Hype4', 1)[0], import_path))
	from hypebundle import *
	
	# ready so run main
	main()
