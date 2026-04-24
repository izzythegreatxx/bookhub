'''Blocklist for storing JWT tokens that have been revoked.'''


from datetime import datetime
from models import db, RevokedToken

def add_to_blocklist(jti: str, expires_at: datetime):
    token = RevokedToken(jti=jti, expires_at=expires_at)
    db.session.add(token)
    db.session.commit()
    
def is_token_revoked(jti: str) -> bool:
    token = RevokedToken.query.filter_by(jti=jti).first()
    if token:
        if token.expires_at < datetime.utcnow():
            # Token has expired, remove it from the blocklist
            db.session.delete(token)
            db.session.commit()
            return False
        return True
    return False


