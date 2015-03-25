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

from rallycu.runners import base
from rallyci.common import virsh
from rallyci import sshutils
from rallyci import utils
import logging


LOG = logging.getLogger(__name__)


class Runner(base.Runner):

    def setup(self, user, **kwargs):
        self.user = user
        self.kwargs = kwargs

    def build(self, stdout_cb):
        self.vm = virsh.VM(self.global_config, self.config)
        self.vm.build()

    def boot(self):
        self.sshconf = {"user": self.user, "host": self.ip}
        LOG.debug("Connecting to %r" % self.sshconf)
        self.ssh = sshutils.SSH(**self.sshconf)
        self.ssh.wait()

    @property
    def ip(self):
        if not hasattr(self, "_ip"):
            self._ip = self.vm.get_ip()
        return self._ip

    def run(self, cmd, stdout_cb, stdin, env):
        for k, v in env.items():
            cmd = "%s=%s " % (k, v) + cmd
        self.ssh.run(cmd, stdin=stdin, **utils.get_stdouterr(stdout_cb))

    def cleanup(self):
        self.vm.cleanup()

    def publish_files(self, job):
        dirs = self.kwargs.get("publish_files", [])
        if not dirs:
            return
        for p in job.publishers:
            publisher = getattr(p, "publish_files", None)
            if publisher:
                for src, dst in dirs:
                    dst = "%s/%s" % (job.name, dst)
                    publisher(self.sshconf, src, dst)
