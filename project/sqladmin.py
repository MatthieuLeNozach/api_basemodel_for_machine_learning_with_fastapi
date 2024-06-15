from typing import ClassVar

from sqladmin import ModelView

from project.fu_core.users import models

# from project.fu_core.users.models import User


# Create a ModelView for the User model
class UserAdmin(ModelView, model=models.User):
    column_list: ClassVar[list] = [
        models.User.id,
        models.User.email,
        models.User.is_active,
        models.User.is_superuser,
    ]
