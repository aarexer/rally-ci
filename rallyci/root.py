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

import asyncio
from concurrent import futures
import logging
import resource
from rallyci.config import Config

LOG = logging.getLogger(__name__)


class Root:
    def __init__(self, loop):
        self.tasks = {}
        self.loop = loop
        self.services = []
        self.providers = {}
        self.task_start_handlers = []
        self.task_end_handlers = []
        self.job_update_handlers = []

    def start_streams(self):
        for stream in self.config.iter_instances("stream"):
            self.services.append(stream)
            stream.start(self)

    def start_services(self):
        for service in self.config.iter_instances("service"):
            self.services.append(service)
            service.start(self)

    def stop_services(self, wait=False):
        fs = []
        for service in self.services + list(self.providers.values()):
            fs.append(service.stop())
        if wait and fs:
            asyncio.wait(fs, return_when=futures.ALL_COMPLETED)
        self.services = []
        self.providers = {}

    def load_config(self):
        self.config = Config(self)
        self.start()

    def start(self):
        self.start_streams()
        self.start_services()
        for prov in self.config.iter_providers():
            self.providers[prov.name] = prov
            prov.start()

    def reload(self):
        try:
            new_config = Config(self)
        except Exception:
            LOG.exception("Error loading new config")
            return
        self.stop_services()
        self.config = new_config
        self.start()

    def task_done(self, future):
        task = self.tasks[future]
        LOG.debug("Completed task: %s" % task)
        for cb in self.task_end_handlers:
            cb(task)
        del (self.tasks[future])

    def job_updated(self, job):
        for cb in self.job_update_handlers:
            cb(job)

    def handle(self, event):
        future = asyncio.async(event.run_jobs(), loop=self.loop)
        self.tasks[future] = event
        future.add_done_callback(self.task_done)
        for cb in self.task_start_handlers:
            cb(event)

    def stop(self):
        LOG.info("Interrupted.")
        self.stop_services(True)
        tasks = list(self.tasks.keys())
        if tasks:
            LOG.info("Waiting for tasks %r." % tasks)
            yield from asyncio.gather(*tasks, return_exceptions=True)
            LOG.info("All tasks finished.")
        self.stop_services(True)
        self.loop.stop()

    def _get_daemon_statistics(self):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return {"type": "daemon-statistics", "memory-used": getattr(usage, "ru_maxrss")}
