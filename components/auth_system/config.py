"""
Configuration for Authentication System

All configuration loaded from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    url: str
    pool_size: int = 10
    pool_timeout: int = 30
    max_overflow: int = 5
    query_timeout: int = 10
    
    @classmethod
    def from_env(cls):
        return cls(
            url=os.getenv("DATABASE_URL", "postgresql://localhost:5432/auth_db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "10"))
        )


@dataclass
class JWTConfig:
    """JWT token configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    @classmethod
    def from_env(cls):
        secret = os.getenv("JWT_SECRET_KEY")
        if not secret:
            raise ValueError("JWT_SECRET_KEY must be set in environment")
        
        return cls(
            secret_key=secret,
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        )


@dataclass
class EmailConfig:
    """Email service configuration"""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str
    use_tls: bool = True
    
    @classmethod
    def from_env(cls):
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "")),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    # Login attempts per window
    login_attempts: int = 10
    login_window_seconds: int = 60
    
    # Registration attempts per window
    register_attempts: int = 5
    register_window_seconds: int = 60
    
    # Password reset attempts per window
    reset_attempts: int = 3
    reset_window_seconds: int = 300  # 5 minutes
    
    @classmethod
    def from_env(cls):
        return cls(
            login_attempts=int(os.getenv("RATE_LIMIT_LOGIN", "10")),
            login_window_seconds=int(os.getenv("RATE_LIMIT_LOGIN_WINDOW", "60")),
            register_attempts=int(os.getenv("RATE_LIMIT_REGISTER", "5")),
            register_window_seconds=int(os.getenv("RATE_LIMIT_REGISTER_WINDOW", "60")),
            reset_attempts=int(os.getenv("RATE_LIMIT_RESET", "3")),
            reset_window_seconds=int(os.getenv("RATE_LIMIT_RESET_WINDOW", "300"))
        )


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration for email service"""
    failure_threshold: int = 5  # Open after 5 failures
    timeout_duration: int = 60  # Stay open for 60 seconds
    expected_exception: Optional[type] = Exception
    
    @classmethod
    def from_env(cls):
        return cls(
            failure_threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
            timeout_duration=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
        )


@dataclass
class SecurityConfig:
    """Security settings"""
    # Password requirements
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special_char: bool = False
    
    # Bcrypt rounds
    bcrypt_rounds: int = 12
    
    # Token settings
    reset_token_expire_hours: int = 1
    
    @classmethod
    def from_env(cls):
        return cls(
            min_password_length=int(os.getenv("MIN_PASSWORD_LENGTH", "8")),
            require_uppercase=os.getenv("REQUIRE_UPPERCASE", "true").lower() == "true",
            require_lowercase=os.getenv("REQUIRE_LOWERCASE", "true").lower() == "true",
            require_digit=os.getenv("REQUIRE_DIGIT", "true").lower() == "true",
            require_special_char=os.getenv("REQUIRE_SPECIAL_CHAR", "false").lower() == "true",
            bcrypt_rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
            reset_token_expire_hours=int(os.getenv("RESET_TOKEN_EXPIRE_HOURS", "1"))
        )


@dataclass
class AppConfig:
    """Main application configuration"""
    database: DatabaseConfig
    jwt: JWTConfig
    email: EmailConfig
    rate_limit: RateLimitConfig
    circuit_breaker: CircuitBreakerConfig
    security: SecurityConfig
    
    # App settings
    debug: bool = False
    environment: str = "development"
    
    @classmethod
    def from_env(cls):
        return cls(
            database=DatabaseConfig.from_env(),
            jwt=JWTConfig.from_env(),
            email=EmailConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
            circuit_breaker=CircuitBreakerConfig.from_env(),
            security=SecurityConfig.from_env(),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development")
        )


# TODO: Load configuration when app starts
# config = AppConfig.from_env()

# Example usage:
if __name__ == "__main__":
    # Create a .env file first with required variables
    try:
        config = AppConfig.from_env()
        print("Configuration loaded successfully!")
        print(f"Database pool size: {config.database.pool_size}")
        print(f"JWT expiry: {config.jwt.access_token_expire_minutes} minutes")
        print(f"Rate limit (login): {config.rate_limit.login_attempts} per {config.rate_limit.login_window_seconds}s")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Make sure to set required environment variables!")
