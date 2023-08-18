import pydantic
from fastapi import HTTPException, Request
from ..app import app
from ..utils import Tags
from ..crud.base import get_collection, get_schema
from ..crud.routes import SimpleMessage

class IngestMetadataConfig(pydantic.BaseModel):
    credential: int | None = None

async def ingest_metadata(identifier: str, config: IngestMetadataConfig, request: Request) -> SimpleMessage:
    ingest_col = get_collection(request, 'metadata_ingestion')
    ds_col = get_collection(request, 'datasource')
    ds = await ds_col.get(identifier)
    if ds is None:
        raise HTTPException(status_code=404, detail='Not Found')
    credential = ds.defaultCredential
    if config.credential:
        credential = config.credential
    cred_col = get_collection(request, 'credential')
    cred = await cred_col.get_by_id(credential)
    if cred is None:
        raise HTTPException(status_code=422, detail='Credential %s not found' % credential)
    job = await ingest_col.create(ingest_col.model_validate(dict(datasource=ds.id, credential=credential)))
    return {
        'detail': 'Submitted metadata ingestion (id=%s)' % job.id
    }

