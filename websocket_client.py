# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2016 EventGhost Project <http://www.eventghost.net/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib27', 'site-packages'))


import websocket
import threading


print '''
you will have the ability to enter these commands
copy and past each of the code blocks including the DONE
be sure to press enter if nothing happens

client.send('TriggerEvent', prefix='Test', suffix='Event', payload='TestEvent')
DONE


client.send('GetLog')
DONE

for i in range(10):
    client.send('TriggerEvent', prefix='TestEvent', suffix=str(i),
        payload='Test Event ' + str(i))
DONE

'''

raw_input('press any key to continue')

websocket.enableTrace(True)

import json

class WebSocketClient(websocket.WebSocketApp):
    def __init__(self):
        kwargs = {
            'on_message' : self.on_message,
            'on_error' : self.on_error,
            'on_close' : self.on_close,
        }
        ws = websocket.WebSocketApp.__init__(self, 'ws://192.168.1.21:6584', **kwargs)

    def send(self, type, *args, **kwargs):
        data = dict(
            Type=type,
            Data=dict(
                Args=args,
                Kwargs=kwargs
            )
        )

        websocket.WebSocketApp.send(self, json.dumps(data))

    def on_open(self, ws):
        data = dict(
            Type="Auth",
            Data=dict(Id="Kevin")
        )
        ws.send(json.dumps(data))

    def on_message(self, ws, message):
        print message
        print json.dumps(json.loads(message), indent=4)

    def on_error(self, _, error):
        print 'ERROR:', error

    def on_close(self, _):
        print 'websocket closed'

    def start(self):
        self.run_forever()


client = WebSocketClient()
t = threading.Thread(target=client.start)
t.start()

evt = threading.Event()
try:
    evt.wait(2)
    while True:
        commands = []
        command = raw_input('Enter Command')

        while command != 'DONE':
            print command
            commands += [command]
            command = raw_input('')

        try:
            exec ('\n'.join(commands))
        except:
            import traceback

            traceback.print_exc()
except KeyboardInterrupt:
    sys.exit(0)
