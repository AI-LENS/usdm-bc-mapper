from cyclopts import App
from pydantic import FilePath

cli = App()


@cli.default
async def usdm_bc_mapper(usdm_path: FilePath, *, config: FilePath | None = None, show_logs: bool = False):
    print("Current Directory :: ")
    print(usdm_path.absolute().as_posix())