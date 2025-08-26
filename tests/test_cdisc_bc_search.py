from usdm_bc_mapper.cdisc_bc_search import CdiscBcIndex


async def test_cdisc_bc_index():
    bc_index = CdiscBcIndex()

    docs = bc_index.search("blood pressure", k=10)
    assert docs[0]["text"] == "Blood Pressure"
    assert docs[0]["metadata"]["index"] == 134

    docs = bc_index.search("urinalysis", k=10)
    assert docs[0]["metadata"]["index"] == 983
