"""Azure OpenAI embeddings + Azure AI Search (hybrid: keyword + vector)."""
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (HnswAlgorithmConfiguration, SearchableField,
                                                   SearchField, SearchFieldDataType, SearchIndex,
                                                   SimpleField, VectorSearch, VectorSearchProfile)
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

from pcbrag.documents import Chunk

FIELDS_TO_RETURN = ["id", "text", "source", "doc_type", "title", "section", "page"]


def openai_client(s):
    if not (s.aoai_endpoint and s.aoai_key):
        raise SystemExit("AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY not set (see .env.example)")
    return AzureOpenAI(azure_endpoint=s.aoai_endpoint, api_key=s.aoai_key,
                       api_version=s.aoai_api_version)


def build_index_definition(name, dim):
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="section", type=SearchFieldDataType.String),
        SimpleField(name="page", type=SearchFieldDataType.Int32),
        SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=dim, vector_search_profile_name="hnsw-profile"),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw")])
    return SearchIndex(name=name, fields=fields, vector_search=vector_search)


class AzureIndex:
    def __init__(self, settings, openai=None, search=None, index_admin=None):
        self.s = settings
        cred = AzureKeyCredential(settings.search_key) if settings.search_key else None
        if search is None and not (settings.search_endpoint and cred):
            raise SystemExit("AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_API_KEY not set (see .env.example)")
        self.openai = openai or openai_client(settings)
        self.search_client = search or SearchClient(settings.search_endpoint, settings.search_index, cred)
        self.index_admin = index_admin or (SearchIndexClient(settings.search_endpoint, cred)
                                           if settings.search_endpoint else None)

    def embed(self, texts, batch=64):
        vectors = []
        for i in range(0, len(texts), batch):
            resp = self.openai.embeddings.create(model=self.s.embed_deployment, input=texts[i:i + batch])
            vectors += [d.embedding for d in resp.data]
        return vectors

    def build(self, chunks, recreate=False):
        if recreate:
            try:
                self.index_admin.delete_index(self.s.search_index)
            except Exception:
                pass  # didn't exist
        self.index_admin.create_or_update_index(build_index_definition(self.s.search_index, self.s.embed_dim))

        vectors = self.embed([c.text for c in chunks])
        docs = [{**c.to_dict(), "embedding": v} for c, v in zip(chunks, vectors)]
        for i in range(0, len(docs), 100):
            results = self.search_client.merge_or_upload_documents(documents=docs[i:i + 100])
            failed = [r.key for r in results if not r.succeeded]
            if failed:
                print(f"warning: {len(failed)} docs failed to upload: {failed[:5]}")
        return self

    def search(self, query, k=5, doc_type=None):
        vector = self.embed([query])[0]
        results = self.search_client.search(
            search_text=query,  # hybrid: keyword part catches exact part numbers / serials
            vector_queries=[VectorizedQuery(vector=vector, k_nearest_neighbors=k * 2, fields="embedding")],
            filter=f"doc_type eq '{doc_type}'" if doc_type else None,
            select=FIELDS_TO_RETURN,
            top=k,
        )
        return [(Chunk(**{f: r.get(f) or ("" if f != "page" else 0) for f in FIELDS_TO_RETURN}),
                 float(r.get("@search.score", 0))) for r in results]
