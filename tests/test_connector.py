from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


def test_download_url_builder() -> None:
    connector = GemeenteOplossingenConnector(
        base_url="https://ris.gemeenteraadhuizen.nl/api/v2/"
    )

    assert (
        connector.build_document_download_url(123)
        == "https://ris.gemeenteraadhuizen.nl/api/v2/documents/123/download"
    )
