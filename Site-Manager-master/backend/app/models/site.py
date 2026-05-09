import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Enum as SAEnum, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.roles import UserRole
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.group import Group
    from app.models.user import User # הוספנו את המודל של המשתמש

class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    sections: Mapped[list["Section"]] = relationship(
        "Section",
        back_populates="site",
        cascade="all, delete-orphan",
        passive_deletes=True # תיקון חשוב לביצועים ומניעת שגיאות
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    group: Mapped["Group"] = relationship("Group", back_populates="sites")


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    classification: Mapped["UserRole"] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # 1. הקשר לאתר (כבר היה לך, הוספתי passive_deletes ב-relationship למעלה)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    site: Mapped["Site"] = relationship("Site", back_populates="sections")

    # 2. הקשר למשתמש (זה מה שהיה חסר!)
    # ה-ondelete="CASCADE" כאן מבטיח שברגע שהמשתמש נמחק - הסקשן הזה נמחק מה-DB
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    creator: Mapped["User"] = relationship("User", back_populates="sections")

    devices: Mapped[list["Device"]] = relationship(
        "Device", 
        back_populates="section", 
        cascade="all, delete-orphan",
        passive_deletes=True
    )