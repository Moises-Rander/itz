"""Armazenamento de mídia em S3-compatível (ex.: Cloudflare R2, AWS S3).

Usado apenas quando ``settings.USE_S3`` é True. Só há conteúdo público
(imagens de cursos, professores, institucional), num único bucket público.
"""
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = None          # R2 não usa ACL; acesso público vem do domínio
    file_overwrite = False
    querystring_auth = False    # URLs públicas (via domínio público do bucket)
