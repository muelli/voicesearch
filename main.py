#!/usr/bin/env python

import logging
import os
from StringIO import StringIO
import sys
from threading import Thread

from gi.repository import Gtk, GLib
from gi.repository import Gst


class FDBuffer(Thread):
    
    BUFSIZE = 1024

    def __init__(self, *args, **kwargs):
        super(FDBuffer, self).__init__(*args, **kwargs)
        self.daemon = True
        # read_fd is for me to read
        # write_fd is others to write
        self.read_fd, self.write_fd = os.pipe()
        
        self.buffer = StringIO()
        
        self.log = logging.getLogger()


    def read(self):
        return os.read(self.read_fd, self.BUFSIZE)


    def run(self, *args, **kwargs):
        self.log.info('Starting to read from %d', self.read_fd)
        data = self.read()
        self.log.info("Finished first read of %d bytes", len(data))
        while data is not None:
            self.log.info("Read %d bytes", len(data))
            self.buffer.write(data)
            data = self.read()

        self.log.info("Finished run")


    def close(self):
        self.buffer.close()


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

            #'filesink location=/tmp/f.flac',
            'fdsink name=fdsink',
        ))
        self.log.debug("Creating pipeline: %s", pipeline)
        self.gst = Gst.parse_launch(pipeline)
        fdsink = self.gst.get_by_name('fdsink')
        
        self.reader = reader = FDBuffer()
        self.reader.start()
        fd = reader.write_fd
        self.log.debug('Reader %s has fd %s', reader, fd)
        #fdsink.fd = fd
        fdsink.set_property("fd", fd)
        self.log.info("fdsink has fd: %d", fdsink.get_property("fd"))
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
            def cb():
                self.stop_recording()
                self.stop_buffer()
                return False
            GLib.idle_add(cb)
            print("Off")


    def start_recording(self, *args, **kwargs):
        self.gst.set_state(Gst.State.PLAYING)
        return False


    def stop_recording(self, *args, **kwargs):
        self.gst.set_state(Gst.State.NULL)
        return False


    def stop_buffer(self, *args, **kwargs):
        self.reader.close()
        self.log.info("Recorded %d bytes", self.reader.buffer.len)
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
