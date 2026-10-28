from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.core.storage import delete_from_s3, download_from_s3, upload_to_s3


def test_upload_to_s3_disabled_when_no_bucket() -> None:
    settings = Settings(s3_bucket_name=None)
    result = upload_to_s3(
        settings,
        key="documents/quotes/Q-0001.pdf",
        data=b"test pdf content",
        content_type="application/pdf",
        tags={"type": "quote", "category": "document"},
    )
    assert result is False


@patch("app.core.storage._build_s3_client")
def test_upload_to_s3_with_tags_and_metadata(mock_build_client) -> None:
    mock_s3 = MagicMock()
    mock_build_client.return_value = mock_s3

    settings = Settings(
        s3_bucket_name="my-price-to-profit-bucket",
        s3_region="us-east-1",
    )
    tags = {
        "type": "quote",
        "category": "document",
        "quote_number": "Q-0001",
        "business_id": "1",
    }
    result = upload_to_s3(
        settings,
        key="documents/quotes/Q-0001.pdf",
        data=b"test-bytes",
        content_type="application/pdf",
        tags=tags,
    )

    assert result is True
    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args.kwargs
    assert call_kwargs["Bucket"] == "my-price-to-profit-bucket"
    assert call_kwargs["Key"] == "documents/quotes/Q-0001.pdf"
    assert call_kwargs["ContentType"] == "application/pdf"
    assert call_kwargs["Body"] == b"test-bytes"
    # Verify tagging format
    assert "type=quote" in call_kwargs["Tagging"]
    assert "category=document" in call_kwargs["Tagging"]
    assert call_kwargs["Metadata"]["type"] == "quote"


@patch("app.core.storage._build_s3_client")
def test_delete_from_s3(mock_build_client) -> None:
    mock_s3 = MagicMock()
    mock_build_client.return_value = mock_s3

    settings = Settings(s3_bucket_name="my-bucket")
    assert delete_from_s3(settings, key="images/logos/test.png") is True
    mock_s3.delete_object.assert_called_once_with(
        Bucket="my-bucket", Key="images/logos/test.png"
    )


@patch("app.core.storage._build_s3_client")
def test_download_from_s3(mock_build_client) -> None:
    mock_s3 = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = b"downloaded-content"
    mock_s3.get_object.return_value = {"Body": mock_body}
    mock_build_client.return_value = mock_s3

    settings = Settings(s3_bucket_name="my-bucket")
    content = download_from_s3(settings, key="documents/invoices/INV-0001.pdf")
    assert content == b"downloaded-content"
