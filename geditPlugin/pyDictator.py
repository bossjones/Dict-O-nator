#!/usr/bin/python3
import sys
sys.path.append('.local/share/gedit/plugins/')
import setlog
logger=setlog.logger
logger.debug('Start Plugin')

from gi.repository import GObject, Gtk, Gedit
ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menu name="PyDictator" action="PyDictator">
          <menuitem name="Clear" action="Clear"/>
          <menuitem name="Logit" action="Logit"/>
        </menu>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class PyDictatorPlugin(GObject.Object,Gedit.WindowActivatable):
    __gtype_name__= "PyDictator"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        logger.debug('Init end')

    def do_activate(self):
        # Insert menu items
        self._insert_menu()
        logger.debug("Finished inserting menu")

    def do_deactivate(self):
        # Remove any installed menu items
        self._remove_menu()
        self._action_group = None
        logger.debug("Finished inserting menu")
        #('6paragraph',None, 'Log it','<Control><Alt>6','Log-it',self.log_action)

    def _insert_menu(self):
        #logger.debug("inside insert menu")
        actions = [
            ('PyDictator',None,'PyDictator'),
            ("Clear", None, "Clear document",'<Control><Alt>1', "Clear the document",self.on_clear_document_activate),
            ("Logit", None, "Log now",'<Control><Alt>2', "Log now ",self.on_logit_activate)
        ]
        # Get the Gtk.UIManager
        manager = self.window.get_ui_manager()
        # Create a new action group
        self._action_group = Gtk.ActionGroup("PyDictatorPluginActions")
        #logger.debug("putting actions")        
        self._action_group.add_actions(actions)
        #logger.debug("put done")
        # Insert the action group
        #logger.debug("adding into actions group")
        manager.insert_action_group(self._action_group)
        # Merge the UI
        #logger.debug("merge into ui")
        self._ui_id = manager.add_ui_from_string(ui_str)        
        
        #oldmethod        
        #self._ui_merge_id = manager.add_ui_from_string(ui_str)
        #manager.ensure_update()
        
    def _remove_menu(self):
        # Get the Gtk.UIManager
        manager = self.window.get_ui_manager()

        # Remove the ui
        manager.remove_ui(self._ui_id)

        # Remove the action group
        manager.remove_action_group(self._action_group)

        # Make sure the manager updates
        manager.ensure_update()
    
    def do_log(self, msg='Default do_log Message'):
        logger.debug(msg)
    
    def do_update_state(self):
        self._action_group.set_sensitive(self.window.get_active_document() != None)

    # Menu activate handlers
    def on_clear_document_activate(self, action):
        doc = self.window.get_active_document()
        if not doc:
            return
        doc.set_text('')

    def on_logit_activate(self, action):
        self.do_log('Executing my action')

