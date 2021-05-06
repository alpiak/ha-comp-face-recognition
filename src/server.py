"Server to serve preview images and pages."
from io import BytesIO
from mimetypes import guess_type

from twisted.web.server import Site, GzipEncoderFactory
from twisted.web.resource import Resource, EncodingResourceWrapper
from twisted.internet import reactor, endpoints
from twisted.web.static import File

from src.storage import Storage

class Server:
    @staticmethod
    def _check_auth(request):
        # TODO: Check auth
        pass

    def __init__(self, port = 3000, storage: Storage = None):
        class StoageResource(File):
            isLeaf = True

            def __init__(self, storage):
                super().__init__('')

                self._storage: Storage = storage
                self._size = 0

            def render_GET(self, request):
                Server._check_auth(request) # TODO: moved to seperated middleware

                self._path = str(request.postpath[0], encoding='utf8')
                self._name = str(request.postpath[1], encoding='utf8')
                self.type, self.encoding = guess_type(self._name)

                return super().render_GET(request)

            def openForReading(self):
                if self._storage is None:
                    raise RuntimeError('No storage mounted.')

                file = storage.get(self._path, self._name, True)

                if isinstance(file, BytesIO):
                    self._size = len(file.getvalue())

                return file
            def isdir(self):
                return False

            def getsize(self):
                return self._size

        class PreviewPageResource(Resource):
            isLeaf = True

            def render_GET(self, request):
                return request.args[b'id'][0]

        root = Resource()
        root.putChild(b'storage', StoageResource(storage))
        root.putChild(b'preview', PreviewPageResource())
        endpoints.TCP4ServerEndpoint(reactor, port).listen(Site(EncodingResourceWrapper(root, [GzipEncoderFactory()])))
        reactor.run()