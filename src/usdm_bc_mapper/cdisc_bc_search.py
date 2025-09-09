from typing import Any, Literal, TypedDict, overload

import bm25s
import polars as pl
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


def build_data() -> pl.DataFrame:
    bc_concepts = pl.scan_csv(
        settings.data_path / "cdisc_biomedical_concepts_latest.csv"
    )
    bc_concepts = bc_concepts.select(
        "bc_id", "short_name", "bc_categories", "synonyms", "definition"
    ).unique()
    specialization_df = pl.scan_csv(
        settings.data_path / "cdisc_sdtm_dataset_specializations_latest.csv"
    )

    specialization_df = specialization_df.select(
        "bc_id", "short_name", "vlm_group_id"
    ).unique()
    df = (
        specialization_df.join(bc_concepts, on=["bc_id"], how="left", suffix="_bc")
        .unique()
        .with_row_index(name="idx")
    )
    return df.collect()


search_result_template = Template(
    """\
{% for item in data -%}
## {{ loop.index }}. {{ item["vlm_group_id"] }}
  {% for k, v in item.items() -%}
  - {{ k }}: {{ v }}
  {% endfor %}
{% endfor %}
"""
)


class CdiscBcIndex:
    def __init__(self) -> None:
        self.data = build_data()
        corpus = []
        for row in self.data.rows(named=True):
            for col in settings.data_search_cols:
                if row[col] is None or len(str(row[col]).strip()) == 0:
                    continue
                corpus.append({
                    "text": str(row[col]).strip(),
                    "metadata": {
                        "index": row["idx"],
                        "colname": col,
                    },
                })
        corpus_text = [doc["text"] for doc in corpus]
        corpus_tokens = bm25s.tokenize(corpus_text, stopwords="en", stemmer=stemmer)
        self.retriever = bm25s.BM25(corpus=corpus)
        self.retriever.index(corpus_tokens)

    @overload
    def search(
        self, query: str, k: int = 10, return_formatted_string: Literal[False] = False
    ) -> list[dict[str, Any]]: ...
    @overload
    def search(
        self, query: str, k: int = 10, return_formatted_string: Literal[True] = True
    ) -> str: ...

    def search(
        self, query: str, k: int = 10, return_formatted_string: bool = False
    ) -> str | list[dict[str, Any]]:
        query_tokens = bm25s.tokenize(query, stopwords="en", stemmer=stemmer)
        results, _ = self.retriever.retrieve(query_tokens, k=k)
        if return_formatted_string:
            return self.format_search_results(results[0])
        else:
            # return [self.data.iloc[item["metadata"]["index"], :] for item in results[0]]
            return [
                self.data.filter(pl.col("idx") == item["metadata"]["index"]).row(
                    0, named=True
                )
                for item in results[0]
            ]

    def format_search_results(self, docs: list[Document]) -> str:
        if len(docs) == 0:
            return "No relevant documents found."
        cols = [
            "vlm_group_id",
            "short_name",
            "bc_categories",
            "synonyms",
            "definition",
        ]
        data = [
            self.data.filter(pl.col("idx") == doc["metadata"]["index"])
            .select(*cols)
            .row(0, named=True)
            for doc in docs
        ]

        return search_result_template.render(
            docs=docs,
            data=data,
        )
