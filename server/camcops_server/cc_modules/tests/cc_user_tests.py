#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_user_tests.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

from pendulum import DateTime as Pendulum

from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_unittest import (
    BasicDatabaseTestCase,
    DemoDatabaseTestCase,
)
from camcops_server.cc_modules.cc_user import (
    SecurityAccountLockout,
    SecurityLoginFailure,
    User,
)


# =============================================================================
# Unit testing
# =============================================================================

class UserTests(DemoDatabaseTestCase):
    """
    Unit tests.
    """
    def test_user(self) -> None:
        self.announce("test_user")
        req = self.req

        SecurityAccountLockout.delete_old_account_lockouts(req)
        self.assertIsInstance(
            SecurityAccountLockout.is_user_locked_out(req, "dummy_user"),
            bool
        )
        self.assertIsInstanceOrNone(
            SecurityAccountLockout.user_locked_out_until(req, "dummy_user"),
            Pendulum
        )

        self.assertIsInstance(
            SecurityLoginFailure.how_many_login_failures(req, "dummy_user"),
            int
        )
        SecurityLoginFailure.clear_login_failures_for_nonexistent_users(req)
        SecurityLoginFailure.clear_dummy_login_failures_if_necessary(req)
        SecurityLoginFailure.clear_dummy_login_failures_if_necessary(req)
        # ... do it twice (we had a bug relating to offset-aware vs
        # offset-naive date/time objects).

        self.assertIsInstance(User.is_username_permissible("some_user"), bool)
        User.take_some_time_mimicking_password_encryption()

        u = self.dbsession.query(User).first()  # type: User
        assert u, "Missing user in demo database!"

        g = self.dbsession.query(Group).first()  # type: Group
        assert g, "Missing group in demo database!"

        self.assertIsInstance(u.is_password_correct("dummy_password"), bool)
        self.assertIsInstance(u.must_agree_terms, bool)
        u.agree_terms(req)
        u.clear_login_failures(req)
        self.assertIsInstance(u.is_locked_out(req), bool)
        self.assertIsInstanceOrNone(u.locked_out_until(req), Pendulum)
        u.enable(req)
        self.assertIsInstance(u.may_login_as_tablet, bool)
        # TODO: cc_user.UserTests: could do more here
        self.assertIsInstance(u.authorized_as_groupadmin, bool)
        self.assertIsInstance(u.may_use_webviewer, bool)
        self.assertIsInstance(u.authorized_to_add_special_note(g.id), bool)
        self.assertIsInstance(u.authorized_to_erase_tasks(g.id), bool)
        self.assertIsInstance(u.authorized_to_dump, bool)
        self.assertIsInstance(u.authorized_for_reports, bool)
        self.assertIsInstance(u.may_view_all_patients_when_unfiltered, bool)
        self.assertIsInstance(u.may_view_no_patients_when_unfiltered, bool)
        self.assertIsInstance(u.may_upload_to_group(g.id), bool)
        self.assertIsInstance(u.may_upload, bool)
        self.assertIsInstance(u.may_register_devices, bool)


class UserPermissionTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        # Deliberately not in alphabetical order to test sorting
        self.group_c = self.create_group("groupc")
        self.group_b = self.create_group("groupb")
        self.group_a = self.create_group("groupa")
        self.group_d = self.create_group("groupd")

    def test_groups_user_may_manage_patients_in(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, may_manage_patients=True)
        self.create_membership(user, self.group_c, may_manage_patients=True)
        self.create_membership(user, self.group_a, may_manage_patients=False)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_may_manage_patients_in)

    def test_ids_of_groups_user_may_report_on(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_a, may_run_reports=False)
        self.create_membership(user, self.group_c, may_run_reports=True)
        self.create_membership(user, self.group_d, may_run_reports=True)

        ids = user.ids_of_groups_user_may_report_on

        self.assertIn(self.group_c.id, ids)
        self.assertIn(self.group_d.id, ids)
        self.assertNotIn(self.group_a.id, ids)
        self.assertNotIn(self.group_b.id, ids)

    def test_ids_of_groups_superuser_may_report_on(self) -> None:
        user = self.create_user(username="test", superuser=True)
        self.dbsession.flush()

        ids = user.ids_of_groups_user_may_report_on

        self.assertIn(self.group_a.id, ids)
        self.assertIn(self.group_b.id, ids)
        self.assertIn(self.group_c.id, ids)
        self.assertIn(self.group_d.id, ids)

    def test_ids_of_groups_user_is_admin_for(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_a, groupadmin=False)
        self.create_membership(user, self.group_c, groupadmin=True)
        self.create_membership(user, self.group_d, groupadmin=True)

        ids = user.ids_of_groups_user_is_admin_for

        self.assertIn(self.group_c.id, ids)
        self.assertIn(self.group_d.id, ids)
        self.assertNotIn(self.group_a.id, ids)
        self.assertNotIn(self.group_b.id, ids)

    def test_ids_of_groups_superuser_is_admin_for(self) -> None:
        user = self.create_user(username="test", superuser=True)
        self.dbsession.flush()

        ids = user.ids_of_groups_user_is_admin_for

        self.assertIn(self.group_a.id, ids)
        self.assertIn(self.group_b.id, ids)
        self.assertIn(self.group_c.id, ids)
        self.assertIn(self.group_d.id, ids)

    def test_names_of_groups_user_is_admin_for(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_a, groupadmin=False)
        self.create_membership(user, self.group_c, groupadmin=True)
        self.create_membership(user, self.group_d, groupadmin=True)

        names = user.names_of_groups_user_is_admin_for

        self.assertIn(self.group_c.name, names)
        self.assertIn(self.group_d.name, names)
        self.assertNotIn(self.group_a.name, names)
        self.assertNotIn(self.group_b.name, names)

    def test_names_of_groups_superuser_is_admin_for(self) -> None:
        user = self.create_user(username="test", superuser=True)
        self.dbsession.flush()

        names = user.names_of_groups_user_is_admin_for

        self.assertIn(self.group_a.name, names)
        self.assertIn(self.group_b.name, names)
        self.assertIn(self.group_c.name, names)
        self.assertIn(self.group_d.name, names)

    def test_groups_user_is_admin_for(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_a, groupadmin=False)
        self.create_membership(user, self.group_c, groupadmin=True)
        self.create_membership(user, self.group_d, groupadmin=True)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_is_admin_for)

    def test_user_may_administer_group(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_a, groupadmin=False)
        self.create_membership(user, self.group_c, groupadmin=True)
        self.create_membership(user, self.group_d, groupadmin=True)
        self.dbsession.commit()

        self.assertFalse(user.may_administer_group(self.group_a.id))
        self.assertTrue(user.may_administer_group(self.group_c.id))
        self.assertTrue(user.may_administer_group(self.group_d.id))

    def test_superuser_may_administer_group(self) -> None:
        user = self.create_user(username="test", superuser=True)
        self.dbsession.flush()

        self.assertTrue(user.may_administer_group(self.group_a.id))
        self.assertTrue(user.may_administer_group(self.group_b.id))
        self.assertTrue(user.may_administer_group(self.group_c.id))
        self.assertTrue(user.may_administer_group(self.group_d.id))

    def test_groups_user_may_dump(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, may_dump_data=True)
        self.create_membership(user, self.group_c, may_dump_data=True)
        self.create_membership(user, self.group_a, may_dump_data=False)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_may_dump)

    def test_groups_user_may_report_on(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, may_run_reports=True)
        self.create_membership(user, self.group_c, may_run_reports=True)
        self.create_membership(user, self.group_a, may_run_reports=False)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_may_report_on)

    def test_groups_user_may_upload_into(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, may_upload=True)
        self.create_membership(user, self.group_c, may_upload=True)
        self.create_membership(user, self.group_a, may_upload=False)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_may_upload_into)

    def test_groups_user_may_add_special_notes(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, may_add_notes=True)
        self.create_membership(user, self.group_c, may_add_notes=True)
        self.create_membership(user, self.group_a, may_add_notes=False)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_may_add_special_notes)

    def test_groups_user_may_see_all_pts_when_unfiltered(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d,
                               view_all_patients_when_unfiltered=True)
        self.create_membership(user, self.group_c,
                               view_all_patients_when_unfiltered=True)
        self.create_membership(user, self.group_a,
                               view_all_patients_when_unfiltered=False)

        self.assertEqual([self.group_c, self.group_d],
                         user.groups_user_may_see_all_pts_when_unfiltered)

    def test_is_a_group_admin(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, groupadmin=True)

        self.assertTrue(user.is_a_groupadmin)

    def test_is_not_a_group_admin(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, groupadmin=False)

        self.assertFalse(user.is_a_groupadmin)

    def test_authorized_as_groupadmin(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, groupadmin=True)

        self.assertTrue(user.authorized_as_groupadmin)

    def test_not_authorized_as_groupadmin(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.create_membership(user, self.group_d, groupadmin=False)

        self.assertFalse(user.authorized_as_groupadmin)

    def test_superuser_authorized_as_groupadmin(self) -> None:
        user = self.create_user(username="test", superuser=True)
        self.dbsession.flush()

        self.assertTrue(user.authorized_as_groupadmin)

    def test_membership_for_group_id(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        ugm = self.create_membership(user, self.group_a)

        self.assertEqual(user.membership_for_group_id(self.group_a.id), ugm)

    def test_no_membership_for_group_id(self) -> None:
        user = self.create_user(username="test")
        self.dbsession.flush()

        self.assertIsNone(user.membership_for_group_id(self.group_a.id))

    # TODO: membership_for_group_id
    # TODO: may_use_webviewer
    # TODO: authorized_to_add_special_note
    # TODO: authorized_to_erase_tasks
    # TODO: authorized_to_dump
    # TODO: authorized_for_reports
    # TODO: may_view_all_patients_when_unfiltered
    # TODO: may_view_no_patients_when_unfiltered
    # TODO: group_ids_that_nonsuperuser_may_see_when_unfiltered
    # TODO: may_upload_to_group
    # TODO: may_upload
    # TODO: may_register_devices
