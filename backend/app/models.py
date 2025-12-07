"""
SQLAlchemy database models for proposals and votes.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Proposal(Base):
    """Proposal model representing investment memos."""
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    ipfs_cid = Column(String, nullable=False)
    confidence = Column(Integer, nullable=False)  # 0-100
    status = Column(String, default="active")  # active, approved, rejected
    yes_votes = Column(Integer, default=0)
    no_votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(Integer, nullable=True)  # Unix timestamp
    proposal_metadata = Column(JSON, default=dict)
    tx_hash = Column(String, nullable=True)  # Blockchain transaction hash
    on_chain_id = Column(Integer, nullable=True)  # ID on the smart contract
    
    def __repr__(self):
        return f"<Proposal(id={self.id}, title='{self.title}', status='{self.status}')>"


class Vote(Base):
    """Vote model for tracking individual votes."""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    voter_address = Column(String, nullable=False)
    vote = Column(Integer, nullable=False)  # 1 for yes, 0 for no
    created_at = Column(DateTime, default=datetime.utcnow)
    tx_hash = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Vote(id={self.id}, proposal_id={self.proposal_id}, vote={self.vote})>"


class User(Base):
    """User model for storing wallet addresses and optional email addresses."""
    __tablename__ = "users"
    
    wallet_address = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(wallet_address='{self.wallet_address}', email='{self.email}')>"


class Organization(Base):
    """Organization model for storing team organizations."""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    ipfs_cid = Column(String, nullable=True)  # CID of organization data on IPFS
    creator_wallet = Column(String, nullable=False)  # Wallet address of creator
    team_members = Column(JSON, nullable=False)  # List of wallet addresses
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', sector='{self.sector}')>"

