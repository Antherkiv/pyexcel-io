"""
    pyexcel_io.manager
    ~~~~~~~~~~~~~~~~~~~

    factory for getting readers and writers

    :copyright: (c) 2014-2017 by Onni Software Ltd.
    :license: New BSD License, see LICENSE for more details
"""
import logging
from collections import defaultdict

from lml.plugin import scan_plugins
from lml.manager import PluginManager, register_class

import pyexcel_io.utils as ioutils
import pyexcel_io.manager as manager
import pyexcel_io.exceptions as exceptions
import pyexcel_io.constants as constants


log = logging.getLogger(__name__)

ERROR_MESSAGE_FORMATTER = "one of these plugins for %s data in '%s': %s"
UPGRADE_MESSAGE = "Please upgrade the plugin '%s' according to \
plugin compactibility table."


class IOManager(PluginManager):
    name = 'pyexcel io plugin'

    def __init__(self):
        self.registry = defaultdict(list)
        self.text_stream_types = []
        self.binary_stream_types = []

    def load_me_later(self, plugin_meta, module_name):
        if not isinstance(plugin_meta, dict):
            plugin = module_name.replace('_', '-')
            raise exceptions.UpgradePlugin(UPGRADE_MESSAGE % plugin)
        library_import_path = "%s.%s" % (module_name, plugin_meta['submodule'])
        for file_type in plugin_meta['file_types']:
            self.registry[file_type].append(
                (library_import_path, plugin_meta['submodule']))
            manager.register_stream_type(file_type, plugin_meta['stream_type'])
            log.debug("pre-register :" + ','.join(plugin_meta['file_types']))

    def load_me_now(self, file_type):
        __file_type = file_type.lower()
        if __file_type in self.registry:
            debug_path = []
            for path in self.registry[__file_type]:
                dynamic_load_library(path)
                debug_path.append(path)
            log.debug("preload :" + __file_type + ":" + ','.join(path))
            # once loaded, forgot it
            self.registry.pop(__file_type)


iomanager = IOManager()
register_class(iomanager)


class Factory(object):
    def __init__(self, action, known_plugins):
        self.registry = defaultdict(dict)
        self.action = action
        self.known_plugins = known_plugins

    def register_a_plugin(self, file_type, plugin, library):
        self.registry[file_type][library] = plugin

    def get_a_plugin(self, file_type, library):
        __file_type = file_type.lower()
        iomanager.load_me_now(__file_type)
        if __file_type in self.registry:
            handler_dict = self.registry[__file_type]
            if library is not None:
                handler_class = handler_dict.get(library, None)
                if handler_class is None:
                    raise Exception("%s is not installed" % library)
            else:
                for _, _handler in handler_dict.items():
                    handler_class = _handler
                    break
            handler = handler_class()
            handler.set_type(__file_type)
            return handler
        plugins = self.known_plugins.get(file_type, None)
        if plugins:
            message = "Please install "
            if len(plugins) > 1:
                message += ERROR_MESSAGE_FORMATTER % (
                    self.action, file_type, ','.join(plugins))
            else:
                message += plugins[0]
            raise exceptions.SupportingPluginAvailableButNotInstalled(message)
        else:
            raise exceptions.NoSupportingPluginFound(
                "No suitable library found for %s" % file_type)


readers = Factory('read', ioutils.AVAILABLE_READERS)
writers = Factory('write', ioutils.AVAILABLE_WRITERS)


def dynamic_load_library(library_import_path):
    plugin = __import__(library_import_path[0])
    submodule = getattr(plugin, library_import_path[1])
    register_readers_and_writers(submodule.exports)


def register_readers_and_writers(plugins):
    __debug_writer_file_types = []
    __debug_reader_file_types = []
    for plugin in plugins:
        the_file_type = plugin['file_type']
        manager.register_a_file_type(
            the_file_type, plugin.get('stream_type', None),
            plugin.get('mime_type', None))
        if 'reader' in plugin:
            readers.register_a_plugin(
                the_file_type, plugin['reader'], plugin['library'])
            __debug_reader_file_types.append(plugin['file_type'])
        if 'writer' in plugin:
            writers.register_a_plugin(
                the_file_type, plugin['writer'], plugin['library'])
            __debug_writer_file_types.append(plugin['file_type'])
        # else:
            # ignored for now
    log.debug("register writers for:" + ",".join(__debug_writer_file_types))
    log.debug("register readers for:" + ",".join(__debug_reader_file_types))


def get_writers():
    return writers.registry.keys()


def load_plugins(prefix, path, black_list):
    scan_plugins(
        prefix, constants.DEFAULT_PLUGIN_NAME,
        path, black_list)
