from logger import logger

from plugin_helpers import path
from flatland import Element, Dict, String, Integer, Boolean, Float, Form, Enum

from microdrop.plugin_manager import IPlugin, IWaveformGenerator, Plugin, \
    implements, PluginGlobals, ScheduleRequest, emit_signal,\
            get_service_instance
from microdrop.app_context import get_app
from microdrop.plugin_helpers import AppDataController, StepOptionsController, \
    get_plugin_info
from microdrop.gui.protocol_grid_controller import ProtocolGridController
import serial_device
from base_node_rpc import SerialProxy


PluginGlobals.push_env('microdrop.managed')

class TestPlugin(Plugin, AppDataController, StepOptionsController):
    """
    This class is automatically registered with the PluginManager.
    """
    implements(IPlugin)
    version = get_plugin_info(path(__file__).parent).version
    plugins_name = get_plugin_info(path(__file__).parent).plugin_name

    '''
    AppFields
    ---------

    A flatland Form specifying application options for the current plugin.
    Note that nested Form objects are not supported.

    Since we subclassed AppDataController, an API is available to access and
    modify these attributes.  This API also provides some nice features
    automatically:
        -all fields listed here will be included in the app options dialog
            (unless properties=dict(show_in_gui=False) is used)
        -the values of these fields will be stored persistently in the microdrop
            config file, in a section named after this plugin's name attribute
    '''

    serial_ports_ = [port for port in serial_device.get_serial_ports()]
    if len(serial_ports_):
        default_port_ = serial_ports_[0]
    else:
        default_port_ = None

    AppFields = Form.of(
        Enum.named('serial_port').using(default=default_port_, optional=True)\
            .valued(*serial_ports_),
    )



    '''
    StepFields
    ---------

    A flatland Form specifying the per step options for the current plugin.
    Note that nested Form objects are not supported.

    Since we subclassed StepOptionsController, an API is available to access and
    modify these attributes.  This API also provides some nice features
    automatically:
        -all fields listed here will be included in the protocol grid view
            (unless properties=dict(show_in_gui=False) is used)
        -the values of these fields will be stored persistently for each step
    '''
    StepFields = Form.of(
        Boolean.named('led_on').using(default=False, optional=True),
    )

    def __init__(self):
        self.name = self.plugins_name
        self.proxy = None

    def on_plugin_enable(self):
        # We need to call AppDataController's on_plugin_enable() to update the
        # application options data.
        AppDataController.on_plugin_enable(self)
        self.on_app_init()
        app_values = self.get_app_values()
        try:
		    self.proxy = SerialProxy(port=app_values['serial_port'])
		    self.proxy.pin_mode(pin=13, mode=1)
		    logger.info('Connected to %s on port %s', self.proxy.properties.display_name,
                        app_values['serial_port'])
        except Exception, e:
            logger.error('Could not connect to base-node-rpc on port %s: %s.',
			     app_values['serial_port'], e)
        if get_app().protocol:
            pgc = get_service_instance(ProtocolGridController, env='microdrop')
            pgc.update_grid()

    def on_plugin_disable(self):
        del self.proxy
        self.proxy = None
        if get_app().protocol:
            pgc = get_service_instance(ProtocolGridController, env='microdrop')
            pgc.update_grid()

    def on_app_init(self):
        pass

    def on_step_options_changed(self, plugin, step_number):
        app = get_app()
        if (plugin == 'wheelerlab.test_plugin'):
            options = self.get_step_options()
            logger.info('[TestPlugin] on_step_options_changed():'
                        '%s step #%d -> %s' % (plugin, step_number, options))

    def on_step_run(self):
        """
        Handler called whenever a step is executed.

        Plugins that handle this signal must emit the on_step_complete
        signal once they have completed the step. The protocol controller
        will wait until all plugins have completed the current step before
        proceeding.
        """
        logger.debug('[TestPlugin] on_step_run()')
        app = get_app()

        if (self.proxy and app.realtime_mode or app.running):
            options = self.get_step_options()
            self.proxy.digital_write(pin=13, value=options['led_on'])
        
        emit_signal('on_step_complete', [self.name, None])

PluginGlobals.pop_env()
