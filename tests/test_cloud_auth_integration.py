"""Tests for cloud authentication integration in get_filesystem()."""

from unittest.mock import Mock, patch

from kirin.utils import get_filesystem


class TestGetFilesystemCloudAuth:
    """Test cloud authentication parameter passing in get_filesystem()."""

    def test_get_filesystem_aws_profile_passing(self):
        """Test that AWS profile parameter is passed through correctly."""
        with patch("kirin.utils._get_s3_filesystem_with_credentials") as mock_s3:
            mock_fs = Mock()
            mock_s3.return_value = mock_fs

            # Test S3 path with AWS profile
            result = get_filesystem("s3://bucket/path", aws_profile="test-profile")

            # Verify the helper was called with the profile
            mock_s3.assert_called_once_with("test-profile")
            assert result == mock_fs

    def test_get_filesystem_gcs_token_project_passing(self):
        """Test that GCS token and project parameters are passed through correctly."""
        with patch("kirin.utils._get_gcs_filesystem_with_credentials") as mock_gcs:
            mock_fs = Mock()
            mock_gcs.return_value = mock_fs

            # Test GCS path with token and project
            result = get_filesystem(
                "gs://bucket/path",
                gcs_token="/path/to/service-account.json",
                gcs_project="test-project"
            )

            # Verify the helper was called with the parameters
            mock_gcs.assert_called_once_with(
                token="/path/to/service-account.json",
                project="test-project"
            )
            assert result == mock_fs

    def test_get_filesystem_azure_credentials_passing(self):
        """Test that Azure credentials are passed through correctly."""
        with patch("kirin.utils._get_azure_filesystem_with_credentials") as mock_azure:
            mock_fs = Mock()
            mock_azure.return_value = mock_fs

            # Test Azure path with credentials
            result = get_filesystem(
                "az://container/path",
                azure_account_name="test-account",
                azure_account_key="test-key",
                azure_connection_string="test-connection"
            )

            # Verify the helper was called with the parameters
            mock_azure.assert_called_once_with(
                account_name="test-account",
                account_key="test-key",
                connection_string="test-connection"
            )
            assert result == mock_fs

    def test_get_filesystem_backward_compatibility(self):
        """Test that existing code without auth parameters still works."""
        with patch("kirin.utils._get_s3_filesystem_with_credentials") as mock_s3:
            mock_fs = Mock()
            mock_s3.return_value = mock_fs

            # Test S3 path without any auth parameters (should use default)
            result = get_filesystem("s3://bucket/path")

            # Verify the helper was called with None (default)
            mock_s3.assert_called_once_with(None)
            assert result == mock_fs

    def test_get_filesystem_local_path_ignores_auth_params(self):
        """Test that local paths ignore cloud auth parameters."""
        with patch("fsspec.filesystem") as mock_fsspec:
            mock_fs = Mock()
            mock_fsspec.return_value = mock_fs

            # Test local path with auth parameters (should be ignored)
            result = get_filesystem(
                "/local/path",
                aws_profile="test-profile",
                gcs_token="test-token",
                azure_account_name="test-account"
            )

            # Verify fsspec was called with 'file' protocol only
            mock_fsspec.assert_called_once_with("file")
            assert result == mock_fs

    def test_get_filesystem_unsupported_protocol_ignores_auth_params(self):
        """Test that unsupported protocols ignore cloud auth parameters."""
        with patch("fsspec.filesystem") as mock_fsspec:
            mock_fs = Mock()
            mock_fsspec.return_value = mock_fs

            # Test unsupported protocol with auth parameters (should be ignored)
            result = get_filesystem(
                "ftp://server/path",
                aws_profile="test-profile",
                gcs_token="test-token",
                azure_account_name="test-account"
            )

            # Verify fsspec was called with the protocol only
            mock_fsspec.assert_called_once_with("ftp")
            assert result == mock_fs

    def test_get_filesystem_mixed_auth_params(self):
        """Test that only relevant auth parameters are passed to each protocol."""
        # Test S3 with mixed params - only AWS should be used
        with patch("kirin.utils._get_s3_filesystem_with_credentials") as mock_s3:
            mock_fs = Mock()
            mock_s3.return_value = mock_fs

            result = get_filesystem(
                "s3://bucket/path",
                aws_profile="aws-profile",
                gcs_token="gcs-token",  # Should be ignored
                azure_account_name="azure-account"  # Should be ignored
            )

            # Only AWS profile should be passed
            mock_s3.assert_called_once_with("aws-profile")
            assert result == mock_fs

        # Test GCS with mixed params - only GCS should be used
        with patch("kirin.utils._get_gcs_filesystem_with_credentials") as mock_gcs:
            mock_fs = Mock()
            mock_gcs.return_value = mock_fs

            result = get_filesystem(
                "gs://bucket/path",
                aws_profile="aws-profile",  # Should be ignored
                gcs_token="gcs-token",
                gcs_project="gcs-project",
                azure_account_name="azure-account"  # Should be ignored
            )

            # Only GCS params should be passed
            mock_gcs.assert_called_once_with(
                token="gcs-token",
                project="gcs-project"
            )
            assert result == mock_fs

    def test_get_filesystem_azure_with_mixed_params(self):
        """Test Azure with mixed params - only Azure should be used."""
        with patch("kirin.utils._get_azure_filesystem_with_credentials") as mock_azure:
            mock_fs = Mock()
            mock_azure.return_value = mock_fs

            result = get_filesystem(
                "az://container/path",
                aws_profile="aws-profile",  # Should be ignored
                gcs_token="gcs-token",  # Should be ignored
                azure_account_name="azure-account",
                azure_account_key="azure-key"
            )

            # Only Azure params should be passed
            mock_azure.assert_called_once_with(
                account_name="azure-account",
                account_key="azure-key",
                connection_string=None
            )
            assert result == mock_fs


class TestCloudAuthHelpers:
    """Test the cloud authentication helper functions."""

    def test_get_gcs_filesystem_with_credentials(self):
        """Test GCS helper function calls cloud_auth.get_gcs_filesystem correctly."""
        with patch("kirin.cloud_auth.get_gcs_filesystem") as mock_get_gcs:
            mock_fs = Mock()
            mock_get_gcs.return_value = mock_fs

            from kirin.utils import _get_gcs_filesystem_with_credentials

            result = _get_gcs_filesystem_with_credentials(
                token="/path/to/service-account.json",
                project="test-project"
            )

            # Verify cloud_auth.get_gcs_filesystem was called with correct params
            mock_get_gcs.assert_called_once_with(
                token="/path/to/service-account.json",
                project="test-project"
            )
            assert result == mock_fs

    def test_get_gcs_filesystem_with_credentials_none_params(self):
        """Test GCS helper function with None parameters."""
        with patch("kirin.cloud_auth.get_gcs_filesystem") as mock_get_gcs:
            mock_fs = Mock()
            mock_get_gcs.return_value = mock_fs

            from kirin.utils import _get_gcs_filesystem_with_credentials

            result = _get_gcs_filesystem_with_credentials()

            # Verify cloud_auth.get_gcs_filesystem was called with None params
            mock_get_gcs.assert_called_once_with(token=None, project=None)
            assert result == mock_fs

    def test_get_azure_filesystem_with_credentials(self):
        """Test Azure helper function calls cloud_auth.get_azure_filesystem."""
        with patch("kirin.cloud_auth.get_azure_filesystem") as mock_get_azure:
            mock_fs = Mock()
            mock_get_azure.return_value = mock_fs

            from kirin.utils import _get_azure_filesystem_with_credentials

            result = _get_azure_filesystem_with_credentials(
                account_name="test-account",
                account_key="test-key",
                connection_string="test-connection"
            )

            # Verify cloud_auth.get_azure_filesystem was called with correct params
            mock_get_azure.assert_called_once_with(
                account_name="test-account",
                account_key="test-key",
                connection_string="test-connection"
            )
            assert result == mock_fs

    def test_get_azure_filesystem_with_credentials_none_params(self):
        """Test Azure helper function with None parameters."""
        with patch("kirin.cloud_auth.get_azure_filesystem") as mock_get_azure:
            mock_fs = Mock()
            mock_get_azure.return_value = mock_fs

            from kirin.utils import _get_azure_filesystem_with_credentials

            result = _get_azure_filesystem_with_credentials()

            # Verify cloud_auth.get_azure_filesystem was called with None params
            mock_get_azure.assert_called_once_with(
                account_name=None,
                account_key=None,
                connection_string=None
            )
            assert result == mock_fs
