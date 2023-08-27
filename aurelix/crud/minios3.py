import minio
from .base import BaseObjectStore
from urllib.parse import urlparse
from datetime import timedelta

class MinioS3(BaseObjectStore):

    def get_client(self) -> minio.Minio:
        parsed = urlparse(self.endpoint_url)
        if parsed.port:
            endpoint = '%s:%s' % (parsed.hostname, parsed.port)
        else:
            endpoint = parsed.hostname

        if parsed.scheme.lower() == 'https':
            secure = True
        else:
            secure = False
        
        return minio.Minio(
            endpoint=endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure
        )

    async def get_presigned_upload_url(self, bucket, key):
        client = self.get_client()
        presigned_url = client.get_presigned_url(method='PUT', bucket_name=bucket, object_name=key, expires=timedelta(seconds=600))
        return presigned_url

    async def get_presigned_download_url(self, bucket, key):
        client = self.get_client()
        presigned_url = client.get_presigned_url(method='GET', bucket_name=bucket, object_name=key, expires=timedelta(seconds=600))
        return presigned_url