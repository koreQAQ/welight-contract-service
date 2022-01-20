class Asset:
    """Mint Asa"""

    def __init__(self, unit_name: str, asset_name: str, url: str, total:int) -> None:
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.url = url
        self.total = total
