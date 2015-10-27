#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import urllib
from urllib import request

from tests.integrated import base


class StatusTestCase(base.IntegrationTest):

    def _get_config(self):
        port = base.get_free_port()
        self.url = "http://localhost:%s" % port
        conf = {
                "service": {
                    "name": "status",
                    "module": "rallyci.services.status",
                    "listen": ["localhost", port],
                }
        }
        return [[conf], [port]]

    def test_index(self):
        r = request.urlopen(self.url)
