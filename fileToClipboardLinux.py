#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

import pygtk 
pygtk.require('2.0') 
import gtk 
import time, urllib, sys 
import os.path 
import shutil 

def uris_to_paths(uris): 

    # convert the uris to files 
    paths = [] 
    for uri in uris: 
        if uri.startswith("file:/"): 
            uri = uri[5:] # keep the "/" 
            while uri.startswith("//"): 
                uri = uri[1:] 

            paths.append(urllib.unquote(uri)) 
        # if it is not "file:", ignore this url! 

    return paths 

def paths_to_uris(paths): 
        return [ "file://"+urllib.quote(path) for path in paths ] 



clipboard=gtk.clipboard_get() 

op = sys.argv[1] 

if op == "--copy" or op == "--cut": 

    files = [os.path.abspath(arg) for arg in sys.argv[2:] ] 
    action = (op == "--copy") and "copy" or "cut" 

    def get_func(clipboard, selectiondata, info, data): 
        txt = action + "\n" + "\n".join(paths_to_uris(files)) 
        print "txt=("+str(txt)+")" 
        selectiondata.set(selectiondata.get_target(), 8, txt) 

    def clear_func(clipboard, data): 
        print "clear_func" 

    # não é suficiente: 
    #targets = [] 
    #targets = gtk.target_list_add_uri_targets(targets, 0) 

    targets = [('x-special/gnome-copied-files',0,0), ("text/uri-list",0,0)] 
    ret = clipboard.set_with_data(targets, get_func, clear_func) 

    print "ret", ret 

elif op == "--paste": 

    destination = sys.argv[2] 

    def callback(clipboard, selectiondata, udata): 

        lines = selectiondata.data.splitlines() 
        action = lines[0].rstrip() 

        uris = lines[1:] 
        files = uris_to_paths(uris) 
        for file in files: 
            print "file", file 

            if action == "copy": 
                shutil.copy(file, destination) 

            else: 
                shutil.move(file, destination) 

        sys.exit() 

    def callback_targets(clipboard, targets, data): 
        print "targets", targets 


    #clipboard.request_targets(callback_targets) 
    clipboard.request_contents("x-special/gnome-copied-files", callback) 

gtk.main() 
