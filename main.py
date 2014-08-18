#!/usr/bin/env python

import logging
import sys

from gi.repository import Gtk, GLib
from gi.repository import Gst


class VoiceSearch(Gtk.Application):
    
    APP_ID = 'org.gnome.VoiceSearch'

    def __init__(self, *args, **kwargs):
        super(VoiceSearch, self).__init__(application_id=self.APP_ID)
        self.connect("activate", self.on_activate)
        self.connect("startup", self.on_startup)
        
        self.log = logging.getLogger()
        
        pipeline = ' ! '.join((
            'pulsesrc',
            'audio/x-raw, rate=44100',
            #'level, message=true',
            'flacenc',
            'filesink location=/tmp/f.flac'
        ))
        self.log.debug("Creating pipeline: %s", pipeline)
        self.gst = Gst.parse_launch(pipeline)
        self.bus = self.gst.get_bus()
        self.bus.connect('message', self.on_message)
        self.bus.add_signal_watch()


    def on_startup(self, app):
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_ABOUT, Gtk.IconSize.BUTTON)
        
        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True
        
        self.button = Gtk.ToggleButton(
            #label='Hello',
            stock=Gtk.STOCK_MEDIA_RECORD,
            #image=image,
            )
        self.button.connect('toggled', self.on_toggled)
        self.window.add(self.button)


    def on_activate(self, app):
        self.window.show_all()
        self.window.present()


    def on_toggled(self, button):
        if button.get_active():
            print("On")
            GLib.idle_add(self.start_recording)
        else:
            GLib.idle_add(self.stop_recording)
            print("Off")


    def start_recording(self, *args, **kwargs):
        self.gst.set_state(Gst.State.PLAYING)
        return False


    def stop_recording(self, *args, **kwargs):
        self.gst.set_state(Gst.State.NULL)
    
        return False


    def on_message(self, message, data):
        self.log.info("Received message %s with data %s", message, data)


def main():
    vs = VoiceSearch()
    return vs.run()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    Gst.init()
    sys.exit(main())
