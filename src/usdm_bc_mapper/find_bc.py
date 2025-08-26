import logging

from usdm_bc_mapper._types import (
    CdiscBcSearch,
    FinalAnswer,
    History,
    LLmResponse,
    Message,
    NciSearch,
    NotFoundAnswer,
)
from usdm_bc_mapper.cdisc_bc_search import CdiscBcIndex
from usdm_bc_mapper.llm import llm
from usdm_bc_mapper.settings import settings

logger = logging.getLogger(__name__)

with open(settings.system_prompt_file, "r") as f:
    system_prompt = f.read()


async def find_biomedical_concept(concept: str):
    """Find the most relevant CDISC biomedical concept for a given medical term.

    Args:
        concept (str): The medical term to search for.
        show_logs (bool): Whether to show detailed logs.

    Returns:
        Prints the most relevant CDISC biomedical concept.
    """

    history = History.model_validate([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": concept},
    ])

    attempts = 0
    bc_index = CdiscBcIndex()

    while attempts < settings.max_ai_lookup_attempts:
        response = await llm(history, LLmResponse)
        if isinstance(response.decision, CdiscBcSearch):
            docs = bc_index.search(
                response.decision.query, return_formatted_string=True
            )
            history.root.append(
                Message.model_validate({"role": "user", "content": docs})
            )
            logger.info(
                f"Search attempt {attempts + 1}: Query: {response.decision.query}"
            )
        elif isinstance(response.decision, NciSearch):
            raise NotImplementedError("NCI Search not implemented yet")
        elif isinstance(response.decision, FinalAnswer) or isinstance(
            response.decision, NotFoundAnswer
        ):
            break
        attempts += 1

    if attempts >= settings.max_ai_lookup_attempts:
        raise RuntimeError("Max attempts reached")
    return response.decision
