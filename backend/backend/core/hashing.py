from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_password(plain_password: str, hashed_password: str):
    """
    This function bool value after verifying the password.
    
    Args:
        - plain_password: user raw password
        - hashed password: saved hash of the user password
        
    Return: compare and return the boolean value.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_password_hash(password: str):
    """
    This function a raw password and return a hash.
    
    Args:
        - password: raw input password
    
    Return: Returns a password hash
    """
    return pwd_context.hash(password)