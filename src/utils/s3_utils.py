import os
import uuid
import boto3
from typing import Literal, Optional, IO
from botocore.config import Config as BotoConfig
from dotenv import load_dotenv

load_dotenv()


class S3Storage:
    """
    Classe genérica para interação com o Amazon S3.
    Usa variáveis de ambiente padrão da AWS ou credenciais explícitas.
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = 'sa-east-1',
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        self._bucket = bucket or os.getenv("S3_BUCKET_NAME")
        if not self._bucket:
            raise ValueError("S3 bucket name must be provided via parameter or S3_BUCKET_NAME env var")

        session_kwargs = {}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
            })
        elif os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            session_kwargs.update({
                "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            })

        self._client = boto3.client(
            "s3",
            region_name=region,
            config=BotoConfig(retries={"max_attempts": 5, "mode": "standard"}),
            **session_kwargs,
        )

    # -------------------------------------------------------------------------
    # 📦 Métodos utilitários
    # -------------------------------------------------------------------------

    @property
    def bucket(self) -> str:
        return self._bucket

    def build_key(
        self,
        filename: str,
        prefix: Optional[str] = None,
        folder: Optional[str] = None,
        unique: bool = True,
    ) -> str:
        """
        Gera uma key única no bucket.
        Exemplo: documents/data_abc123.csv
        """
        name, ext = filename.rsplit(".", 1)
        unique_name = f"{name}_{uuid.uuid4().hex[:8]}.{ext}" if unique else filename

        parts = [p for p in [prefix, folder, unique_name] if p]
        return "/".join(parts)

    # -------------------------------------------------------------------------
    # ☁️ Operações principais
    # -------------------------------------------------------------------------

    def upload_fileobj(
        self,
        key: str,
        fileobj: IO,
        content_type: Optional[str] = None,
        extra_args: Optional[dict] = None,
    ) -> str:
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        if extra_args:
            extra.update(extra_args)

        self._client.upload_fileobj(fileobj, self._bucket, key, ExtraArgs=extra)
        return f"s3://{self._bucket}/{key}"

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        extra_args: Optional[dict] = None,
    ) -> str:
        """Upload direto de bytes"""
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        if extra_args:
            extra.update(extra_args)

        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)
        return f"s3://{self._bucket}/{key}"

    def download_to_memory(self, key: str) -> bytes:
        """Baixa um arquivo do S3 e retorna os bytes."""
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def download_to_file(self, key: str, local_path: str) -> None:
        """Baixa um arquivo para o disco."""
        self._client.download_file(self._bucket, key, local_path)

    def list_files(self, prefix: Optional[str] = None) -> list[str]:
        """Lista arquivos de um prefixo."""
        response = self._client.list_objects_v2(Bucket=self._bucket, Prefix=prefix or "")
        contents = response.get("Contents", [])
        return [obj["Key"] for obj in contents]

    def delete_file(self, key: str) -> None:
        """Remove um arquivo do bucket."""
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def presigned_get_url(self, key: str, expires: int = 3600) -> str:
        """Gera URL pré-assinada de leitura."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires,
        )

    def presigned_put_url(self, key: str, expires: int = 3600, content_type: Optional[str] = None) -> str:
        """Gera URL pré-assinada de upload."""
        params = {"Bucket": self._bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type
        return self._client.generate_presigned_url("put_object", Params=params, ExpiresIn=expires)
