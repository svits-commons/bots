from tortoise import fields
from tortoise.models import Model

from utils import utcnow


class Report(Model):
    ID = fields.BigIntField(pk=True)
    user_id = fields.IntField(null=False)
    username = fields.CharField(max_length=52)
    created_at = fields.FloatField(default=utcnow())

    def __repr__(self):
        return f'Report ID={self.ID}, user_id={self.user_id}, created_at={self.created_at}'
