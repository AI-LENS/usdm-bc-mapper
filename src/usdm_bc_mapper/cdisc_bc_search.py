from typing import Literal, TypedDict, overload

import bm25s
import pandas as pd
import Stemmer
from jinja2 import Template

from usdm_bc_mapper.settings import settings

stemmer = Stemmer.Stemmer("english")


class DocumentMetadata(TypedDict):
    index: str
    colname: str


class Document(TypedDict):
    text: str
    metadata: DocumentMetadata


def build_retriever(df: pd.DataFrame) -> bm25s.BM25:
    corpus = []
    for idx, row in df.iterrows():
        for col in settings.data_search_cols:
            if pd.isna(row[col]) or len(str(row[col]).strip()) == 0:
                continue
            corpus.append({
                "text": str(row[col]).strip(),
                "metadata": {
                    "index": idx,
                    "colname": col,
                },
            })
    corpus_text = [doc["text"] for doc in corpus]
    corpus_tokens = bm25s.tokenize(corpus_text, stopwords="en", stemmer=stemmer)
    retriever = bm25s.BM25(corpus=corpus)
    retriever.index(corpus_tokens)
    return retriever


search_result_template = Template(
    """\
{% for doc in docs -%}
## {{ loop.index }}. {{ df.iloc[doc["metadata"]["index"]]["bc_id"] }}
  {% for col in cols -%}
  - {{ col }}: {{ df.iloc[doc["metadata"]["index"]][col] }}
  {% endfor %}
{% endfor %}
"""
)


class CdiscBcIndex:
    def __init__(self) -> None:
        self.data = pd.read_csv(settings.data_path)
        self.data = self.data.drop_duplicates(
            subset=settings.data_search_cols
        ).reset_index(drop=True)
        self.retriever = build_retriever(self.data)

    @overload
    def search(
        self, query: str, k: int = 10, return_formatted_string: Literal[False] = False
    ) -> list[Document]: ...
    @overload
    def search(
        self, query: str, k: int = 10, return_formatted_string: Literal[True] = True
    ) -> str: ...

    def search(
        self, query: str, k: int = 10, return_formatted_string: bool = False
    ) -> str | list[Document]:
        query_tokens = bm25s.tokenize(query, stopwords="en", stemmer=stemmer)
        results, _ = self.retriever.retrieve(query_tokens, k=k)
        if return_formatted_string:
            return self.format_search_results(results[0])
        else:
            return results[0]

    def format_search_results(self, docs: list[Document]) -> str:
        if len(docs) == 0:
            return "No relevant documents found."

        return search_result_template.render(
            docs=docs, df=self.data, cols=settings.data_search_cols
        )
