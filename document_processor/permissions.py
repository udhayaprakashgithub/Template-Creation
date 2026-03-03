from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_roles = ()

    def test_func(self):
        profile = getattr(self.request.user, "profile", None)
        return bool(profile and profile.role in self.required_roles)


class AdminRequiredMixin(RoleRequiredMixin):
    required_roles = ("admin",)


class UserOrAdminRequiredMixin(RoleRequiredMixin):
    required_roles = ("admin", "user")
