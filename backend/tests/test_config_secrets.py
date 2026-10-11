"""Production credential guards; run independently without database fixtures."""

import pytest

from app.core.config import Settings


@pytest.mark.parametrize("environment", ["production", "staging"])
@pytest.mark.parametrize("password", ["", "quant_password", "change_me"])
def test_deployment_rejects_database_placeholders(environment, password):
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        Settings(
            ENVIRONMENT=environment,
            SECRET_KEY="deployment-secret-" + "x" * 32,
            POSTGRES_PASSWORD=password,
            CORS_ORIGINS=["https://quant.example.com"],
            _env_file=None,
        )


@pytest.mark.parametrize("environment", ["production", "staging"])
@pytest.mark.parametrize(
    "secret",
    ["replace_with_secure_secret", "dev-only-insecure-secret-key-change-in-env-file"],
)
def test_deployment_rejects_development_secrets(environment, secret):
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            ENVIRONMENT=environment,
            SECRET_KEY=secret,
            POSTGRES_PASSWORD="test-only-deployment-password",
            CORS_ORIGINS=["https://quant.example.com"],
            _env_file=None,
        )


def test_deployment_accepts_explicit_credentials_and_disables_custom_code():
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="deployment-secret-" + "x" * 32,
        POSTGRES_PASSWORD="test-only-deployment-password",
        CORS_ORIGINS=["https://quant.example.com"],
        ALLOW_CUSTOM_STRATEGY_CODE_EXEC=True,
        _env_file=None,
    )
    assert settings.ALLOW_CUSTOM_STRATEGY_CODE_EXEC is False
