"""
camcops_server/cc_modules/cc_testfactories.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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

**Factory Boy SQL Alchemy test factories.**

"""

from cardinal_pythonlib.datetimefunc import (
    convert_datetime_to_utc,
    format_datetime,
)
import factory
from faker import Faker
import pendulum

from camcops_server.cc_modules.cc_constants import DateFormat, ERA_NOW
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_testproviders import register_all_providers
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    PatientTaskScheduleEmail,
    TaskSchedule,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_user import User


class Fake:
    # Factory Boy has its own interface to Faker (factory.Faker()). This
    # takes a function to be called at object generation time and as far as I
    # can tell this doesn't support being able to create fake data based on
    # other fake attributes such as notes for a patient. You can work
    # around this by adding a lot of logic to the factories. To me it makes
    # sense to keep the factories simple and do as much as possible of the
    # content generation in the providers. So we call Faker directly instead.
    en_gb = Faker("en_GB")  # For UK postcodes, phone numbers etc
    en_us = Faker("en_US")  # en_GB gives Lorem ipsum for pad words.


register_all_providers(Fake.en_gb)


# sqlalchemy_session gets poked in by DemoRequestCase.setUp()
class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session_persistence = "commit"


class DeviceFactory(BaseFactory):
    class Meta:
        model = Device

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Test device {n}")


class GroupFactory(BaseFactory):
    class Meta:
        model = Group

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Group {n}")


class AnyIdNumGroupFactory(GroupFactory):
    upload_policy = "sex and anyidnum"
    finalize_policy = "sex and anyidnum"


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user{n + 1}")
    hashedpw = ""


class GenericTabletRecordFactory(BaseFactory):
    class Meta:
        exclude = ("default_iso_datetime",)
        abstract = True

    default_iso_datetime = "1970-01-01T12:00"

    _device = factory.SubFactory(DeviceFactory)
    _group = factory.SubFactory(AnyIdNumGroupFactory)
    _adding_user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def _when_added_exact(self) -> pendulum.DateTime:
        return pendulum.parse(self.default_iso_datetime)

    @factory.lazy_attribute
    def _when_added_batch_utc(self) -> pendulum.DateTime:
        era_time = pendulum.parse(self.default_iso_datetime)
        return convert_datetime_to_utc(era_time)

    @factory.lazy_attribute
    def _era(self) -> str:
        era_time = pendulum.parse(self.default_iso_datetime)
        return format_datetime(era_time, DateFormat.ISO8601)

    @factory.lazy_attribute
    def _current(self) -> bool:
        # _current = True gets ignored for some reason
        return True


class PatientFactory(GenericTabletRecordFactory):
    class Meta:
        model = Patient

    id = factory.Sequence(lambda n: n + 1)
    sex = factory.LazyFunction(Fake.en_gb.sex)


class ServerCreatedPatientFactory(PatientFactory):
    @factory.lazy_attribute
    def _device(self) -> Device:
        # Should have been created in BasicDatabaseTestCase.setUp
        return Device.get_server_device(
            ServerCreatedPatientFactory._meta.sqlalchemy_session
        )

    @factory.lazy_attribute
    def _era(self) -> str:
        return ERA_NOW


class IdNumDefinitionFactory(BaseFactory):
    class Meta:
        model = IdNumDefinition

    which_idnum = factory.Sequence(lambda n: n + 1)


class NHSIdNumDefinitionFactory(IdNumDefinitionFactory):
    description = "NHS number"
    short_description = "NHS#"
    hl7_assigning_authority = "NHS"
    hl7_id_type = "NHSN"


class StudyIdNumDefinitionFactory(IdNumDefinitionFactory):
    description = "Study number"
    short_description = "Study"


class RioIdNumDefinitionFactory(IdNumDefinitionFactory):
    description = "RiO number"
    short_description = "RiO"
    hl7_assigning_authority = "CPFT"
    hl7_id_type = "CPRiO"


class PatientIdNumFactory(GenericTabletRecordFactory):
    class Meta:
        model = PatientIdNum

    id = factory.Sequence(lambda n: n + 1)
    patient = factory.SubFactory(PatientFactory)
    patient_id = factory.SelfAttribute("patient.id")
    _group = factory.SelfAttribute("patient._group")
    _device = factory.SelfAttribute("patient._device")


class NHSPatientIdNumFactory(PatientIdNumFactory):
    class Meta:
        exclude = PatientIdNumFactory._meta.exclude + ("idnum",)

    idnum = factory.SubFactory(NHSIdNumDefinitionFactory)

    which_idnum = factory.SelfAttribute("idnum.which_idnum")
    idnum_value = factory.LazyFunction(Fake.en_gb.nhs_number)


class RioPatientIdNumFactory(PatientIdNumFactory):
    class Meta:
        exclude = PatientIdNumFactory._meta.exclude + ("idnum",)

    idnum = factory.SubFactory(RioIdNumDefinitionFactory)

    which_idnum = factory.SelfAttribute("idnum.which_idnum")
    idnum_value = factory.Sequence(lambda n: n + 10000)


class StudyPatientIdNumFactory(PatientIdNumFactory):
    class Meta:
        exclude = PatientIdNumFactory._meta.exclude + ("idnum",)

    idnum = factory.SubFactory(StudyIdNumDefinitionFactory)

    which_idnum = factory.SelfAttribute("idnum.which_idnum")
    idnum_value = factory.Sequence(lambda n: n + 1000)


class ServerCreatedPatientIdNumFactory(PatientIdNumFactory):
    patient = factory.SubFactory(ServerCreatedPatientFactory)

    @factory.lazy_attribute
    def _device(self) -> Device:
        # Should have been created in BasicDatabaseTestCase.setUp
        return Device.get_server_device(
            ServerCreatedPatientIdNumFactory._meta.sqlalchemy_session
        )

    @factory.lazy_attribute
    def _era(self) -> str:
        return ERA_NOW


class ServerCreatedNHSPatientIdNumFactory(
    ServerCreatedPatientIdNumFactory, NHSPatientIdNumFactory
):
    class Meta:
        exclude = (
            ServerCreatedPatientIdNumFactory._meta.exclude
            + NHSPatientIdNumFactory._meta.exclude
        )


class ServerCreatedRioPatientIdNumFactory(
    ServerCreatedPatientIdNumFactory, RioPatientIdNumFactory
):
    class Meta:
        exclude = (
            ServerCreatedPatientIdNumFactory._meta.exclude
            + RioPatientIdNumFactory._meta.exclude
        )


class ServerCreatedStudyPatientIdNumFactory(
    ServerCreatedPatientIdNumFactory, StudyPatientIdNumFactory
):
    class Meta:
        exclude = (
            ServerCreatedPatientIdNumFactory._meta.exclude
            + StudyPatientIdNumFactory._meta.exclude
        )


class TaskScheduleFactory(BaseFactory):
    class Meta:
        model = TaskSchedule

    group = factory.SubFactory(GroupFactory)


class TaskScheduleItemFactory(BaseFactory):
    class Meta:
        model = TaskScheduleItem

    task_schedule = factory.SubFactory(TaskScheduleFactory)


class PatientTaskScheduleFactory(BaseFactory):
    class Meta:
        model = PatientTaskSchedule

    task_schedule = factory.SubFactory(TaskScheduleFactory)
    # If patient has not been set explicitly,
    # ensure Patient and TaskSchedule end up in the same group
    start_datetime = None
    patient = factory.SubFactory(
        ServerCreatedPatientFactory,
        _group=factory.SelfAttribute("..task_schedule.group"),
    )


class EmailFactory(BaseFactory):
    class Meta:
        model = Email

    @factory.post_generation
    def sent_at_utc(
        self, create: bool, sent_at_utc: pendulum.DateTime, **kwargs
    ) -> None:
        if not create:
            return

        self.sent_at_utc = sent_at_utc

    @factory.post_generation
    def sent(self, create: bool, sent: bool, **kwargs) -> None:
        if not create:
            return

        self.sent = sent


class PatientTaskScheduleEmailFactory(BaseFactory):
    class Meta:
        model = PatientTaskScheduleEmail


class UserGroupMembershipFactory(BaseFactory):
    class Meta:
        model = UserGroupMembership

    @factory.post_generation
    def may_run_reports(
        self, create: bool, may_run_reports: bool, **kwargs
    ) -> None:
        if not create:
            return

        self.may_run_reports = may_run_reports
