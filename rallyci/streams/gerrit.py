# Copyright 2015: Mirantis Inc.
# All Rights Reserved.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from rallyci.streams import base

import json
import time
import subprocess
import logging


LOG = logging.getLogger(__name__)
PIDFILE = "/var/log/rally-ci/gerrit-ssh.pid"


class Stream(base.Stream):

    def start_client(self):
        cmd = "ssh -p %(port)d %(username)s@%(hostname)s gerrit stream-events" % \
              self.config["ssh"]
        self.pipe = subprocess.Popen(cmd.split(" "),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)

    def generate(self):
        try:
            while True:
                for line in self._gen():
                    yield line
                time.sleep(10)
        finally:
            self.pipe.terminate()

    def _gen(self):
        self.start_client()
        with open(self.config.get("pidfile", PIDFILE), "w") as pidfile:
            pidfile.write(str(self.pipe.pid))
        for line in iter(self.pipe.stdout.readline, b''):
            if not line:
                break
            yield(json.loads(line))
