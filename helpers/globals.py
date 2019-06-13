import logging.config


def initialize():
	global logger

	# create logger and load the logging configuration
	logger = logging.getLogger('Admin_Client')
	# logging.basicConfig(
	#	format='%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s')
	logging.config.fileConfig('logging.ini')
