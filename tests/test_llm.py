from typing import Literal
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import BaseModel

from usdm_bc_mapper._types import History
from usdm_bc_mapper.llm import llm


class BioMedicalConceptOutput(BaseModel):
    analysis: str
    concept_id: Literal["C94866", "C54706", "C139218"]


@patch("usdm_bc_mapper.llm.client")
async def test_llm_biomedical_concept_selection(mock_client):
    """Test that the LLM can correctly select a biomedical concept based on user input."""
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.output_parsed = BioMedicalConceptOutput(
        analysis="Based on the user input 'Blood Pressure', this clearly refers to the measurement of blood pressure against blood vessel walls.",
        concept_id="C54706",
    )

    mock_client.responses.parse = AsyncMock(return_value=mock_response)

    system_prompt = """Choose the correct bio-medical concept id for the user given activity.

Here is a list of available concepts:
1. C94866 - Blood Flow Rate: The volume of blood per unit time passing through a specified location, such as a point in a blood vessel or an entire organ. Units are ml/sec.
2. C54706 - Blood Pressure: The pressure of the circulating blood against the walls of the blood vessels.
3. C139218 - Body Fat Percentage: The amount of an individual's total body mass that is fat, expressed as a percent.

Give your analysis, supporting your decision to choose the specific bio-medical concept. Then select the appropriate concept ID.
"""

    output = await llm(
        history=History.model_validate([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Blood Pressure"},
        ]),
        output_model=BioMedicalConceptOutput,
    )

    # Assertions on the output
    assert isinstance(output, BioMedicalConceptOutput)
    assert output.concept_id == "C54706"
    assert output.analysis is not None
    assert len(output.analysis) > 0
