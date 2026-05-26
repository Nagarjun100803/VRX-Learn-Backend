from passlib.hash import argon2  # type: ignore[reportAttributeAccessIssue]


class PasswordHasher:
    "Helper class to perfrom the password hashing and verifying."

    def hash_password(self, raw_password: str) -> str:
        return argon2.hash(raw_password)

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        return argon2.verify(raw_password, hashed_password)
