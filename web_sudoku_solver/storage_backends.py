#storage_backends.py
#https://www.ordinarycoders.com/blog/article/serve-django-static-and-media-files-in-production

from storages.backends.s3boto3 import S3Boto3Storage
class MediaStorage(S3Boto3Storage):
    location = 'static/media'
    file_overwrite = True
