#!/usr/bin/env python

"""camcops_server/cc_modules/tests/cc_fhir_tests.py

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

import datetime
import json
import logging
from typing import Dict
from unittest import mock

from cardinal_pythonlib.httpconst import HttpMethod
from cardinal_pythonlib.nhs import generate_random_nhs_number
import pendulum
from requests.exceptions import HTTPError

from camcops_server.cc_modules.cc_constants import FHIRConst as Fc
from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportedTaskFhir,
)
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportRecipientInfo
from camcops_server.cc_modules.cc_fhir import (
    FhirExportException,
    FhirTaskExporter,
)
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_unittest import DemoDatabaseTestCase
from camcops_server.tasks.apeqpt import Apeqpt
from camcops_server.tasks.bmi import Bmi
from camcops_server.tasks.diagnosis import (
    DiagnosisIcd10,
    DiagnosisIcd10Item,
    DiagnosisIcd9CM,
    DiagnosisIcd9CMItem,
)
from camcops_server.tasks.phq9 import Phq9

log = logging.getLogger()


# =============================================================================
# Constants
# =============================================================================

TEST_NHS_NUMBER = generate_random_nhs_number()
TEST_RIO_NUMBER = 12345
TEST_FORENAME = "Gwendolyn"
TEST_SURNAME = "Ryann"
TEST_SEX = "F"


# =============================================================================
# Helper classes
# =============================================================================

class MockFhirTaskExporter(FhirTaskExporter):
    pass


class MockFhirResponse(mock.Mock):
    def __init__(self, response_json: Dict):
        super().__init__(
            text=json.dumps(response_json),
            json=mock.Mock(return_value=response_json)
        )


class FhirExportTestCase(DemoDatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        recipientinfo = ExportRecipientInfo()

        self.recipient = ExportRecipient(recipientinfo)
        self.recipient.primary_idnum = self.rio_iddef.which_idnum
        self.recipient.fhir_api_url = "https://www.example.com/fhir"

        # auto increment doesn't work for BigInteger with SQLite
        self.recipient.id = 1
        self.recipient.recipient_name = "test"

        self.camcops_root_url = self.req.route_url(Routes.HOME).rstrip("/")
        # ... no trailing slash


# =============================================================================
# A generic patient-based task: PHQ9
# =============================================================================

class FhirTaskExporterPhq9Tests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.patient = self.create_patient(
            forename=TEST_FORENAME,
            surname=TEST_SURNAME,
            sex=TEST_SEX
        )
        self.patient_nhs = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER
        )
        self.patient_rio = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.rio_iddef.which_idnum,
            idnum_value=TEST_RIO_NUMBER
        )

        self.task = Phq9()
        self.apply_standard_task_fields(self.task)
        self.task.q1 = 0
        self.task.q2 = 1
        self.task.q3 = 2
        self.task.q4 = 3
        self.task.q5 = 0
        self.task.q6 = 1
        self.task.q7 = 2
        self.task.q8 = 3
        self.task.q9 = 0
        self.task.q10 = 3
        self.task.patient_id = self.patient.id
        self.task.save_with_next_available_id(self.req, self.patient._device_id)
        self.dbsession.commit()

    def test_patient_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        self.assertEqual(sent_json[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_BUNDLE)
        self.assertEqual(sent_json[Fc.TYPE], Fc.TRANSACTION)

        patient = sent_json[Fc.ENTRY][0][Fc.RESOURCE]
        self.assertEqual(patient[Fc.RESOURCE_TYPE], Fc.RESOURCE_TYPE_PATIENT)

        identifier = patient[Fc.IDENTIFIER]
        which_idnum = self.patient_rio.which_idnum
        idnum_value = self.patient_rio.idnum_value

        iddef_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_PATIENT_ID_SYSTEM}/{which_idnum}"
        )

        self.assertEqual(identifier[0][Fc.SYSTEM], iddef_url)
        self.assertEqual(identifier[0][Fc.VALUE], str(idnum_value))

        self.assertEqual(patient[Fc.NAME][0][Fc.NAME_FAMILY],
                         self.patient.surname)
        self.assertEqual(patient[Fc.NAME][0][Fc.NAME_GIVEN],
                         [self.patient.forename])
        self.assertEqual(patient[Fc.GENDER], Fc.GENDER_FEMALE)

        request = sent_json[Fc.ENTRY][0][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], Fc.RESOURCE_TYPE_PATIENT)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST],
            f"{Fc.IDENTIFIER}={iddef_url}|{idnum_value}"
        )

    def test_questionnaire_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        questionnaire = sent_json[Fc.ENTRY][1][Fc.RESOURCE]
        self.assertEqual(questionnaire[Fc.RESOURCE_TYPE],
                         Fc.RESOURCE_TYPE_QUESTIONNAIRE)
        self.assertEqual(questionnaire[Fc.STATUS], Fc.QSTATUS_ACTIVE)

        identifier = questionnaire[Fc.IDENTIFIER]

        questionnaire_url = (
            f"{self.camcops_root_url}/{Routes.FHIR_QUESTIONNAIRE}"
        )
        self.assertEqual(identifier[0][Fc.SYSTEM], questionnaire_url)
        self.assertEqual(identifier[0][Fc.VALUE], "phq9")

        question_1 = questionnaire[Fc.ITEM][0]
        question_10 = questionnaire[Fc.ITEM][9]
        self.assertEqual(question_1[Fc.LINK_ID], "q1")
        self.assertEqual(question_1[Fc.TEXT],
                         "1. Little interest or pleasure in doing things")
        self.assertEqual(question_1[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)

        options = question_1[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Not at all")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Several days")

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.DISPLAY],
                         "More than half the days")

        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.CODE], "3")
        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Nearly every day")

        self.assertEqual(question_10[Fc.LINK_ID], "q10")
        self.assertEqual(
            question_10[Fc.TEXT],
            ("10. If you checked off any problems, how difficult have these "
             "problems made it for you to do your work, take care of things "
             "at home, or get along with other people?")
        )
        self.assertEqual(question_10[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = question_10[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Not difficult at all")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Somewhat difficult")

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Very difficult")

        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.CODE], "3")
        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Extremely difficult")

        self.assertEqual(len(questionnaire[Fc.ITEM]), 10)

        request = sent_json[Fc.ENTRY][1][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], Fc.RESOURCE_TYPE_QUESTIONNAIRE)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST],
            f"{Fc.IDENTIFIER}={questionnaire_url}|phq9"
        )

    def test_questionnaire_response_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        response = sent_json[Fc.ENTRY][2][Fc.RESOURCE]
        self.assertEqual(response[Fc.RESOURCE_TYPE],
                         Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE)
        self.assertEqual(
            response[Fc.QUESTIONNAIRE],
            (
                f"{self.camcops_root_url}/"
                f"{Routes.FHIR_QUESTIONNAIRE}|phq9"
            )
        )
        self.assertEqual(response[Fc.AUTHORED],
                         self.task.when_created.isoformat())
        self.assertEqual(response[Fc.STATUS], Fc.QSTATUS_COMPLETED)

        subject = response[Fc.SUBJECT]
        identifier = subject[Fc.IDENTIFIER]
        self.assertEqual(subject[Fc.TYPE], Fc.RESOURCE_TYPE_PATIENT)
        which_idnum = self.patient_rio.which_idnum
        idnum_value = self.patient_rio.idnum_value

        iddef_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_PATIENT_ID_SYSTEM}/{which_idnum}"
        )
        self.assertEqual(identifier[Fc.SYSTEM], iddef_url)
        self.assertEqual(identifier[Fc.VALUE], str(idnum_value))

        request = sent_json[Fc.ENTRY][2][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL],
                         Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE)
        response_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_QUESTIONNAIRE_RESPONSE}/phq9"
        )
        self.assertEqual(
            request[Fc.IF_NONE_EXIST],
            f"{Fc.IDENTIFIER}={response_url}|{self.task._pk}"
        )

        item_1 = response[Fc.ITEM][0]
        item_10 = response[Fc.ITEM][9]
        self.assertEqual(item_1[Fc.LINK_ID], "q1")
        self.assertEqual(item_1[Fc.TEXT],
                         "1. Little interest or pleasure in doing things")
        answer_1 = item_1[Fc.ANSWER][0]
        # noinspection PyUnresolvedReferences
        self.assertEqual(answer_1[Fc.VALUE_INTEGER], self.task.q1)

        self.assertEqual(item_10[Fc.LINK_ID], "q10")
        self.assertEqual(
            item_10[Fc.TEXT],
            ("10. If you checked off any problems, how difficult have these "
             "problems made it for you to do your work, take care of things "
             "at home, or get along with other people?")
        )
        answer_10 = item_10[Fc.ANSWER][0]
        self.assertEqual(answer_10[Fc.VALUE_INTEGER], self.task.q10)

        self.assertEqual(len(response[Fc.ITEM]), 10)

    # noinspection PyUnresolvedReferences
    def test_exported_task_saved(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        # auto increment doesn't work for BigInteger with SQLite
        exported_task.id = 1
        self.dbsession.add(exported_task)

        exported_task_fhir = ExportedTaskFhir(exported_task)
        self.dbsession.add(exported_task_fhir)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.RESOURCE_TYPE: Fc.RESOURCE_TYPE_BUNDLE,
            Fc.ID: 'cae48957-e7e6-4649-97f8-0a882076ad0a',
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
            Fc.LINK: [
                {
                    Fc.RELATION: Fc.SELF,
                    Fc.URL: 'http://localhost:8080/fhir'
                }
            ],
            Fc.ENTRY: [
                {
                    Fc.RESPONSE: {
                        Fc.STATUS: Fc.RESPONSE_STATUS_200_OK,
                        Fc.LOCATION: 'Patient/1/_history/1',
                        Fc.ETAG: '1'
                    }
                },
                {
                    Fc.RESPONSE: {
                        Fc.STATUS: Fc.RESPONSE_STATUS_200_OK,
                        Fc.LOCATION: 'Questionnaire/26/_history/1',
                        Fc.ETAG: '1'
                    }
                },
                {
                    Fc.RESPONSE: {
                        Fc.STATUS: Fc.RESPONSE_STATUS_201_CREATED,
                        Fc.LOCATION: 'QuestionnaireResponse/42/_history/1',
                        Fc.ETAG: '1',
                        Fc.LAST_MODIFIED: '2021-05-24T09:30:11.098+00:00'
                    }
                }
            ]
        }

        with mock.patch.object(exporter.client.server, "post_json",
                               return_value=MockFhirResponse(response_json)):
            exporter.export_task()

        self.dbsession.commit()

        entries = exported_task_fhir.entries  # type: List[ExportedTaskFhirEntry]  # noqa

        entries.sort(key=lambda e: e.location)

        self.assertEqual(entries[0].status, Fc.RESPONSE_STATUS_200_OK)
        self.assertEqual(entries[0].location, "Patient/1/_history/1")
        self.assertEqual(entries[0].etag, "1")

        self.assertEqual(entries[1].status, Fc.RESPONSE_STATUS_200_OK)
        self.assertEqual(entries[1].location, "Questionnaire/26/_history/1")
        self.assertEqual(entries[1].etag, "1")

        self.assertEqual(entries[2].status, Fc.RESPONSE_STATUS_201_CREATED)
        self.assertEqual(entries[2].location,
                         "QuestionnaireResponse/42/_history/1")
        self.assertEqual(entries[2].etag, "1")
        self.assertEqual(entries[2].last_modified,
                         datetime.datetime(2021, 5, 24, 9, 30, 11, 98000))

    # def test_raises_when_task_does_not_support(self) -> None:
    #     exported_task = ExportedTask(task=self.task, recipient=self.recipient)
    #     exported_task_fhir = ExportedTaskFhir(exported_task)
    #
    #     exporter = MockFhirTaskExporter(self.req, exported_task_fhir)
    #
    #     errmsg = "Something is not implemented"
    #     with mock.patch.object(self.task,
    #                            "get_fhir_bundle_entries") as mock_task:
    #         mock_task.side_effect = NotImplementedError(errmsg)
    #
    #         with self.assertRaises(FhirExportException) as cm:
    #             exporter.export_task()
    #
    #         message = str(cm.exception)
    #         self.assertIn(errmsg, message)

    def test_raises_when_http_error(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        errmsg = "Something bad happened"
        with mock.patch.object(
                exporter.client.server, "post_json",
                side_effect=HTTPError(response=mock.Mock(text=errmsg))):
            with self.assertRaises(FhirExportException) as cm:
                exporter.export_task()

            message = str(cm.exception)
            self.assertIn(errmsg, message)

    def test_raises_when_fhirclient_raises(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        exporter.client.server = None
        with self.assertRaises(FhirExportException) as cm:
            exporter.export_task()

            message = str(cm.exception)
            self.assertIn("Cannot create a resource without a server", message)

    def test_raises_for_missing_api_url(self) -> None:
        self.recipient.fhir_api_url = ""
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        with self.assertRaises(FhirExportException) as cm:
            FhirTaskExporter(self.req, exported_task_fhir)

        message = str(cm.exception)
        self.assertIn("must be initialized with `base_uri`", message)


# =============================================================================
# A generic patient-based task: APEQPT
# =============================================================================

OFFERED_PREFERENCE = "Have you been offered your preference?"
SATISFIED_ASSESSMENT = "How satisfied were you with your assessment"
TELL_US = (
    "Please use this space to tell us about your experience of our service"
)
PREFER_ANY = "Do you prefer any of the treatments among the options available?"
GIVEN_INFO = (
    "Were you given information about options for choosing a "
    "treatment that is appropriate for your problems?"
)


class FhirTaskExporterAnonymousTests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.task = Apeqpt()
        self.apply_standard_task_fields(self.task)
        self.task.q_datetime = pendulum.now()
        self.task.q1_choice = 0
        self.task.q2_choice = 1
        self.task.q3_choice = 2
        self.task.q1_satisfaction = 3
        self.task.q2_satisfaction = "Service experience"

        self.task.save_with_next_available_id(self.req,
                                              self.server_device.id)
        self.dbsession.commit()

    def test_questionnaire_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        questionnaire = sent_json[Fc.ENTRY][0][Fc.RESOURCE]
        self.assertEqual(questionnaire[Fc.RESOURCE_TYPE],
                         Fc.RESOURCE_TYPE_QUESTIONNAIRE)
        self.assertEqual(questionnaire[Fc.STATUS], Fc.QSTATUS_ACTIVE)

        identifier = questionnaire[Fc.IDENTIFIER]

        questionnaire_url = (
            f"{self.camcops_root_url}/{Routes.FHIR_QUESTIONNAIRE}"
        )
        self.assertEqual(identifier[0][Fc.SYSTEM], questionnaire_url)
        self.assertEqual(identifier[0][Fc.VALUE], "apeqpt")

        q_datetime = questionnaire[Fc.ITEM][0]

        q1_choice = questionnaire[Fc.ITEM][1]
        q2_choice = questionnaire[Fc.ITEM][2]
        q3_choice = questionnaire[Fc.ITEM][3]

        q1_satisfaction = questionnaire[Fc.ITEM][4]
        q2_satisfaction = questionnaire[Fc.ITEM][5]

        # q_datetime
        self.assertEqual(q_datetime[Fc.LINK_ID], "q_datetime")
        self.assertEqual(q_datetime[Fc.TEXT],
                         "Date &amp; Time the Assessment Tool was Completed")
        self.assertEqual(q_datetime[Fc.TYPE], Fc.QITEM_TYPE_DATETIME)

        # q1_choice
        self.assertEqual(q1_choice[Fc.LINK_ID], "q1_choice")
        self.assertEqual(q1_choice[Fc.TEXT], GIVEN_INFO)
        self.assertEqual(q1_choice[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)

        options = q1_choice[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "No")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Yes")

        # q2_choice
        self.assertEqual(q2_choice[Fc.LINK_ID], "q2_choice")
        self.assertEqual(q2_choice[Fc.TEXT], PREFER_ANY)
        self.assertEqual(q2_choice[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = q2_choice[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "No")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Yes")

        # q3_choice
        self.assertEqual(q3_choice[Fc.LINK_ID], "q3_choice")
        self.assertEqual(q3_choice[Fc.TEXT], OFFERED_PREFERENCE)
        self.assertEqual(q3_choice[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = q3_choice[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY], "No")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY], "Yes")

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.DISPLAY], "N/A")

        # q1_satisfaction
        self.assertEqual(q1_satisfaction[Fc.LINK_ID], "q1_satisfaction")
        self.assertEqual(q1_satisfaction[Fc.TEXT], SATISFIED_ASSESSMENT)
        self.assertEqual(q1_satisfaction[Fc.TYPE], Fc.QITEM_TYPE_CHOICE)
        options = q1_satisfaction[Fc.ANSWER_OPTION]
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.CODE], "0")
        self.assertEqual(options[0][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Not at all Satisfied")

        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.CODE], "1")
        self.assertEqual(options[1][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Not Satisfied")

        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.CODE], "2")
        self.assertEqual(options[2][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Neither Satisfied nor Dissatisfied")

        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.CODE], "3")
        self.assertEqual(options[3][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Mostly Satisfied")

        self.assertEqual(options[4][Fc.VALUE_CODING][Fc.CODE], "4")
        self.assertEqual(options[4][Fc.VALUE_CODING][Fc.DISPLAY],
                         "Completely Satisfied")

        # q2 satisfaction
        self.assertEqual(q2_satisfaction[Fc.LINK_ID], "q2_satisfaction")
        self.assertEqual(q2_satisfaction[Fc.TEXT], TELL_US)
        self.assertEqual(q2_satisfaction[Fc.TYPE], Fc.QITEM_TYPE_STRING)

        self.assertEqual(len(questionnaire[Fc.ITEM]), 6)

        request = sent_json[Fc.ENTRY][0][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], Fc.RESOURCE_TYPE_QUESTIONNAIRE)
        self.assertEqual(
            request[Fc.IF_NONE_EXIST],
            f"{Fc.IDENTIFIER}={questionnaire_url}|apeqpt"
        )

    def test_questionnaire_response_exported(self) -> None:
        exported_task = ExportedTask(task=self.task, recipient=self.recipient)
        exported_task_fhir = ExportedTaskFhir(exported_task)

        exporter = MockFhirTaskExporter(self.req, exported_task_fhir)

        response_json = {
            Fc.TYPE: Fc.TRANSACTION_RESPONSE,
        }

        with mock.patch.object(
                exporter.client.server, "post_json",
                return_value=MockFhirResponse(response_json)) as mock_post:
            exporter.export_task()

        args, kwargs = mock_post.call_args

        sent_json = args[1]

        response = sent_json[Fc.ENTRY][1][Fc.RESOURCE]
        self.assertEqual(response[Fc.RESOURCE_TYPE],
                         Fc.RESOURCE_TYPE_QUESTIONNAIRE_RESPONSE)
        self.assertEqual(
            response[Fc.QUESTIONNAIRE],
            (
                f"{self.camcops_root_url}/"
                f"{Routes.FHIR_QUESTIONNAIRE}|apeqpt"
            )
        )
        self.assertEqual(response[Fc.AUTHORED],
                         self.task.when_created.isoformat())
        self.assertEqual(response[Fc.STATUS], Fc.QSTATUS_COMPLETED)

        request = sent_json[Fc.ENTRY][1][Fc.REQUEST]
        self.assertEqual(request[Fc.METHOD], HttpMethod.POST)
        self.assertEqual(request[Fc.URL], "QuestionnaireResponse")
        response_url = (
            f"{self.camcops_root_url}/"
            f"{Routes.FHIR_QUESTIONNAIRE_RESPONSE}/apeqpt"
        )
        self.assertEqual(
            request[Fc.IF_NONE_EXIST],
            f"{Fc.IDENTIFIER}={response_url}|{self.task._pk}"
        )

        q_datetime = response[Fc.ITEM][0]

        q1_choice = response[Fc.ITEM][1]
        q2_choice = response[Fc.ITEM][2]
        q3_choice = response[Fc.ITEM][3]

        q1_satisfaction = response[Fc.ITEM][4]
        q2_satisfaction = response[Fc.ITEM][5]

        # q_datetime
        self.assertEqual(q_datetime[Fc.LINK_ID], "q_datetime")
        self.assertEqual(q_datetime[Fc.TEXT],
                         "Date &amp; Time the Assessment Tool was Completed")
        q_datetime_answer = q_datetime[Fc.ANSWER][0]
        self.assertEqual(q_datetime_answer[Fc.VALUE_DATE_TIME],
                         self.task.q_datetime.isoformat())

        # q1_choice
        self.assertEqual(q1_choice[Fc.LINK_ID], "q1_choice")
        self.assertEqual(q1_choice[Fc.TEXT], GIVEN_INFO)
        q1_choice_answer = q1_choice[Fc.ANSWER][0]
        self.assertEqual(q1_choice_answer[Fc.VALUE_INTEGER],
                         self.task.q1_choice)

        # q2_choice
        self.assertEqual(q2_choice[Fc.LINK_ID], "q2_choice")
        self.assertEqual(q2_choice[Fc.TEXT], PREFER_ANY)
        q2_choice_answer = q2_choice[Fc.ANSWER][0]
        self.assertEqual(q2_choice_answer[Fc.VALUE_INTEGER],
                         self.task.q2_choice)

        # q3_choice
        self.assertEqual(q3_choice[Fc.LINK_ID], "q3_choice")
        self.assertEqual(q3_choice[Fc.TEXT], OFFERED_PREFERENCE)
        q3_choice_answer = q3_choice[Fc.ANSWER][0]
        self.assertEqual(q3_choice_answer[Fc.VALUE_INTEGER],
                         self.task.q3_choice)

        # q1_satisfaction
        self.assertEqual(q1_satisfaction[Fc.LINK_ID], "q1_satisfaction")
        self.assertEqual(q1_satisfaction[Fc.TEXT], SATISFIED_ASSESSMENT)
        q1_satisfaction_answer = q1_satisfaction[Fc.ANSWER][0]
        self.assertEqual(q1_satisfaction_answer[Fc.VALUE_INTEGER],
                         self.task.q1_satisfaction)

        # q2 satisfaction
        self.assertEqual(q2_satisfaction[Fc.LINK_ID], "q2_satisfaction")
        self.assertEqual(q2_satisfaction[Fc.TEXT], TELL_US)
        q2_satisfaction_answer = q2_satisfaction[Fc.ANSWER][0]
        self.assertEqual(q2_satisfaction_answer[Fc.VALUE_STRING],
                         self.task.q2_satisfaction)

        self.assertEqual(len(response[Fc.ITEM]), 6)


# =============================================================================
# Tasks that add their own special details
# =============================================================================

class FhirTaskExporterBMITests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.patient = self.create_patient(
            forename=TEST_FORENAME,
            surname=TEST_SURNAME,
            sex=TEST_SEX
        )
        self.patient_nhs = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER
        )
        self.patient_rio = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.rio_iddef.which_idnum,
            idnum_value=TEST_RIO_NUMBER
        )

        self.task = Bmi()
        self.apply_standard_task_fields(self.task)
        self.task.mass_kg = 70
        self.task.height_m = 1.8
        self.task.waist_cm = 82
        self.task.patient_id = self.patient.id
        self.task.save_with_next_available_id(self.req, self.patient._device_id)
        self.dbsession.commit()

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req,
            self.recipient,
            skip_docs_if_other_content=True
        )
        bundle_str = json.dumps(bundle.as_json(), indent=4)
        log.debug(f"Bundle:\n{bundle_str}")
        # The test is that it doesn't crash.


class FhirTaskExporterDiagnosisIcd10Tests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.patient = self.create_patient(
            forename=TEST_FORENAME,
            surname=TEST_SURNAME,
            sex=TEST_SEX
        )
        self.patient_nhs = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER
        )
        self.patient_rio = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.rio_iddef.which_idnum,
            idnum_value=TEST_RIO_NUMBER
        )

        self.task = DiagnosisIcd10()
        self.apply_standard_task_fields(self.task)
        self.task.patient_id = self.patient.id
        self.task.save_with_next_available_id(self.req, self.patient._device_id)
        self.dbsession.commit()

        # noinspection PyArgumentList
        item1 = DiagnosisIcd10Item(
            diagnosis_icd10_id=self.task.id,
            seqnum=1,
            code="F33.30",
            description="Recurrent depressive disorder, current episode "
                        "severe with psychotic symptoms: "
                        "with mood-congruent psychotic symptoms",
            comment="Cotard's syndrome"
        )
        self.apply_standard_db_fields(item1)
        item1.save_with_next_available_id(self.req, self.task._device_id)
        # noinspection PyArgumentList
        item2 = DiagnosisIcd10Item(
            diagnosis_icd10_id=self.task.id,
            seqnum=2,
            code="F43.1",
            description="Post-traumatic stress disorder"
        )
        self.apply_standard_db_fields(item2)
        item2.save_with_next_available_id(self.req, self.task._device_id)

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req,
            self.recipient,
            skip_docs_if_other_content=True
        )
        bundle_str = json.dumps(bundle.as_json(), indent=4)
        log.debug(f"Bundle:\n{bundle_str}")
        # The test is that it doesn't crash.


class FhirTaskExporterDiagnosisIcd9CMTests(FhirExportTestCase):
    def create_tasks(self) -> None:
        self.patient = self.create_patient(
            forename=TEST_FORENAME,
            surname=TEST_SURNAME,
            sex=TEST_SEX
        )
        self.patient_nhs = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.nhs_iddef.which_idnum,
            idnum_value=TEST_NHS_NUMBER
        )
        self.patient_rio = self.create_patient_idnum(
            patient_id=self.patient.id,
            which_idnum=self.rio_iddef.which_idnum,
            idnum_value=TEST_RIO_NUMBER
        )

        self.task = DiagnosisIcd9CM()
        self.apply_standard_task_fields(self.task)
        self.task.patient_id = self.patient.id
        self.task.save_with_next_available_id(self.req, self.patient._device_id)
        self.dbsession.commit()

        # noinspection PyArgumentList
        item1 = DiagnosisIcd9CMItem(
            diagnosis_icd10_id=self.task.id,
            seqnum=1,
            code="290.4",
            description="Vascular dementia",
            comment="or perhaps mixed dementia"
        )
        self.apply_standard_db_fields(item1)
        item1.save_with_next_available_id(self.req, self.task._device_id)
        # noinspection PyArgumentList
        item2 = DiagnosisIcd9CMItem(
            diagnosis_icd10_id=self.task.id,
            seqnum=2,
            code="303.0",
            description="Acute alcoholic intoxication"
        )
        self.apply_standard_db_fields(item2)
        item2.save_with_next_available_id(self.req, self.task._device_id)

    def test_observations(self) -> None:
        bundle = self.task.get_fhir_bundle(
            self.req,
            self.recipient,
            skip_docs_if_other_content=True
        )
        bundle_str = json.dumps(bundle.as_json(), indent=4)
        log.debug(f"Bundle:\n{bundle_str}")
        # The test is that it doesn't crash.
