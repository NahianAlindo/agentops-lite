"""Payload schema for points in the Qdrant documentation collection.

The collection name, vector size and distance come from settings (default
``documentation_chunks``, 384 dimensions, cosine).
"""

from pydantic import BaseModel, ConfigDict, Field

from app.core.limits import MAX_SOURCE_LOCATION_LENGTH, MAX_TITLE_LENGTH


class DocumentChunkPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Stable identifier of the source document; with chunk_index it determines the point id.
    doc_id: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    source_url: str = Field(min_length=1, max_length=MAX_SOURCE_LOCATION_LENGTH)
    section_title: str = Field(max_length=MAX_TITLE_LENGTH)
    text: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    # Version of the indexed documentation, so stale chunks can be found and replaced.
    doc_version: str = Field(min_length=1, max_length=50)
