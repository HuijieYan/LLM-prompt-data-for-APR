You need to fix a bug in a python code snippet.

The buggy source code is following, and you should follow all specifications in comment if there exists comment:

	def generate_context(
		context_file='cookiecutter.json', default_context=None, extra_context=None
	):
		"""Generate the context for a Cookiecutter project template.

		Loads the JSON file as a Python object, with key being the JSON filename.

		:param context_file: JSON file containing key/value pairs for populating
			the cookiecutter's variables.
		:param default_context: Dictionary containing config to take into account.
		:param extra_context: Dictionary containing configuration overrides
		"""
		context = OrderedDict([])

		try:
			with open(context_file) as file_handle:
				obj = json.load(file_handle, object_pairs_hook=OrderedDict)
		except ValueError as e:
			# JSON decoding error.  Let's throw a new exception that is more
			# friendly for the developer or user.
			full_fpath = os.path.abspath(context_file)
			json_exc_message = str(e)
			our_exc_message = (
				'JSON decoding error while loading "{0}".  Decoding'
				' error details: "{1}"'.format(full_fpath, json_exc_message)
			)
			raise ContextDecodingException(our_exc_message)

		# Add the Python object to the context dictionary
		file_name = os.path.split(context_file)[1]
		file_stem = file_name.split('.')[0]
		context[file_stem] = obj

		# Overwrite context variable defaults with the default context from the
		# user's global config, if available
		if default_context:
			apply_overwrites_to_context(obj, default_context)
		if extra_context:
			apply_overwrites_to_context(obj, extra_context)

		logger.debug('Context generated is %s', context)
		return context



The raised issue description for this bug is: 'When using cookiecutter on the cookiecutter I am working on (https://github.com/agateau/cookiecutter-qt-app) and using the default values except for selecting the MIT license, the author name appeared wrongly encoded both in the prompt default value and in the generated LICENSE file. Explicitly setting the encoding to utf-8 when reading the context file fixes this.'.



You need to provide a drop-in replacement, with 'minimum changes to source code' that 'pass failed test' while 'won't affect other already passed tests'. And the fixed patch can be directly used in original project.