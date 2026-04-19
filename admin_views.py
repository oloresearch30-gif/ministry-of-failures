from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_required
from flask import redirect, url_for, request, flash
from models import db, AdminUser, IndexCard


class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return super().index()


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.active

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))


class AdminUserView(SecureModelView):
    column_list         = ['username', 'email', 'role', 'active', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters      = ['role', 'active']
    form_excluded_columns = ['password_hash', 'created_at']
    can_delete          = True

    def is_accessible(self):
        return (current_user.is_authenticated and
                current_user.active and
                current_user.role == 'superadmin')

    def on_model_change(self, form, model, is_created):
        if hasattr(form, 'password') and form.password.data:
            model.set_password(form.password.data)


class IndexCardView(SecureModelView):
    column_list            = ['number', 'title_en', 'active', 'updated_at']
    column_searchable_list = ['title_si', 'title_en', 'body']
    column_filters         = ['active']
    column_default_sort    = ('number', False)
    form_widget_args = {
        'body': {'rows': 8},
        'title_si': {'rows': 2},
    }
    can_export = True


def init_admin(app):
    admin = Admin(
        app,
        name='Ministry of Failures — Admin',
        template_mode='bootstrap4',
        index_view=SecureAdminIndexView()
    )
    admin.add_view(IndexCardView(IndexCard, db.session, name='Index Cards', category='Content'))
    admin.add_view(AdminUserView(AdminUser, db.session, name='Admin Users', category='Settings'))
    return admin