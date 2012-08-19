# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cql.cursor import Cursor
from cql.query import cql_quote
from cql.cassandra import Cassandra
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol
from cql.cassandra.ttypes import AuthenticationRequest
from cql.apivalues import ProgrammingError, NotSupportedError


class Connection(object):
    cql_major_version = 2

    def __init__(self, host, port, keyspace, user=None, password=None, cql_version=None):
        """
        Params:
        * host .........: hostname of Cassandra node.
        * port .........: port number to connect to.
        * keyspace .....: keyspace to connect to.
        * user .........: username used in authentication (optional).
        * password .....: password used in authentication (optional).
        * cql_version...: CQL version to use (optional).
        """
        self.host = host
        self.port = port
        self.keyspace = keyspace

        socket = TSocket.TSocket(host, port)
        self.transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocolAccelerated(self.transport)
        self.client = Cassandra.Client(protocol)

        socket.open()
        self.open_socket = True

        if user and password:
            credentials = {"username": user, "password": password}
            self.client.login(AuthenticationRequest(credentials=credentials))

        self.remote_thrift_version = tuple(map(int, self.client.describe_version().split('.')))

        if cql_version:
            self.client.set_cql_version(cql_version)
            try:
                self.cql_major_version = int(cql_version.split('.')[0])
            except ValueError:
                pass

        if keyspace:
            c = self.cursor()
            c.execute('USE %s;' % cql_quote(keyspace))
            c.close()

    def __str__(self):
        return "{host: '%s:%s', keyspace: '%s'}"%(self.host,self.port,self.keyspace)

    ###
    # Connection API
    ###

    def close(self):
        if not self.open_socket:
            return

        self.transport.close()
        self.open_socket = False

    def commit(self):
        """
        'Database modules that do not support transactions should
          implement this method with void functionality.'
        """
        return

    def rollback(self):
        raise NotSupportedError("Rollback functionality not present in Cassandra.")

    def cursor(self):
        if not self.open_socket:
            raise ProgrammingError("Connection has been closed.")
        return Cursor(self)

# TODO: Pull connections out of a pool instead.
def connect(host, port=9160, keyspace='system', user=None, password=None, cql_version=None):
    return connection.Connection(host, port, keyspace, user, password, cql_version)
