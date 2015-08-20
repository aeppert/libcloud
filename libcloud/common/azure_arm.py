# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import time
import urllib

from libcloud.common.base import ConnectionUserAndKey, JsonResponse, RawResponse, LoggingHTTPSConnection
from libcloud.httplib_ssl import LibcloudHTTPSConnection

class AzureBaseDriver(object):
    name = "Microsoft Azure Resource Management API"


class AzureResourceManagementConnection(ConnectionUserAndKey):
    """
    Represents a single connection to Azure
    """

    driver = AzureBaseDriver
    name = 'Azure AD Auth'
    responseCls = JsonResponse
    rawResponseCls = RawResponse
    host = 'management.azure.com'
    login_host = 'login.windows.net'
    login_resource = 'https://management.core.windows.net/'

    def __init__(self, key, secret, secure=True, tenant_id=None, subscription_id=None, **kwargs):
        super(AzureResourceManagementConnection, self).__init__(key, secret, **kwargs)
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id

    def add_default_headers(self, headers):
        headers['Content-Type'] = "application/json"
        headers['Authorization'] = "Bearer %s" % self.access_token
        return headers

    def encode_data(self, data):
        """Encode data to JSON"""
        return json.dumps(data)

    def get_token_from_credentials(self):
        """Log in and get bearer token used to authorize API requests."""

        conn = LibcloudHTTPSConnection(self.login_host)
        conn.connect()
        params = urllib.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.user_id,
            "client_secret": self.key,
            "resource": self.login_resource
        })
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        conn.request("POST", "/%s/oauth2/token" % self.tenant_id, params, headers)
        js = JsonResponse(conn.getresponse(), conn)
        self.access_token = js.object["access_token"]
        self.expires_on = js.object["expires_on"]

    def connect(self, **kwargs):
        self.get_token_from_credentials()
        return super(AzureResourceManagementConnection, self).connect(**kwargs)

    def request(self, action, params=None, data=None, headers=None,
                method='GET', raw=False):

        # Log in again if the token has expired or is going to expire soon
        # (next 5 minutes).
        if (time.time()+300) >= self.expires_on:
            self.get_token_from_credentials(self)

        return super(AzureResourceManagementConnection, self).request(action, params=params,
                                                               data=data, headers=headers,
                                                               method=method, raw=raw)