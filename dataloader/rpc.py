import os
import xmlrpc.server

class DataLoaderService:
    def find(self, town):
        return {'town': town, 'added': '2018-01-01', 'tracked': True, 'properties': []}

server = xmlrpc.server.SimpleXMLRPCServer(('0.0.0.0', int(os.environ['RPC_PORT'])))
server.register_instance(DataLoaderService())
server.serve_forever()