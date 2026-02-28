from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.orm import declared_attr, DeclarativeBase


class MSModel(DeclarativeBase):
    """
    MACRO SIGNAGE MODEL

    This class is used to provide a common interface for all models.
    """
    __allow_unmapped__ = True

    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower()

    @declared_attr
    def id(cls):
        for base in cls.__mro__[1:-1]:
            if getattr(base, '__table__', None) is not None:
                rtype = sa.ForeignKey(base.id, ondelete='CASCADE')
                break
        else:
            rtype = sa.Integer()
        return sa.Column(rtype, primary_key=True)

    @declared_attr
    def created_at(cls):
        return sa.Column(sa.DateTime, default=sa.func.now())

    @declared_attr
    def updated_at(cls):
        return sa.Column(sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())


db = SQLAlchemy(model_class=MSModel)

extensions = [
    db,
]
