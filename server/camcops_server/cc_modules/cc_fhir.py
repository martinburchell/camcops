#!/usr/bin/env python

# noinspection HttpUrlsUsage
"""
camcops_server/cc_modules/cc_fhir.py

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

**Implements communication with a FHIR server.**

Fast Healthcare Interoperability Resources

https://www.hl7.org/fhir/

Our implementation exports patients and tasks as FHIR Patient, Questionnaire
and QuestionnaireResponse resources.

Currently PHQ9 and APEQPT (anonymous) are supported. Each task and patient (if
appropriate is sent to the FHIR server in a single "transaction" Bundle)
The resources are given a unique identifier based on the URL of the CamCOPS
server.

We use the Python client https://github.com/smart-on-fhir/client-py/.
This only supports one version of the FHIR specification (currently 4.0.1).

Tested with HAPI FHIR server locally, which was installed from instructions at
https://github.com/hapifhir/hapi-fhir-jpaserver-starter (Docker):

.. code-block:: bash

    cd hapi-fhir-jpaserver-starter
    sudo docker run -p 8080:8080 hapiproject/hapi:latest

with the following entry in the CamCOPS export recipient configuration:

.. code-block:: none

    FHIR_API_URL = http://localhost:8080/fhir

There are also public sandboxes at:

- http://hapi.fhir.org/baseR4
- https://r4.smarthealthit.org (errors when exporting questionnaire responses)

"""

from typing import Dict, TYPE_CHECKING

from fhirclient import client
from fhirclient.models.bundle import Bundle
from requests.exceptions import HTTPError

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_exportmodels import ExportedTaskFhir
    from camcops_server.cc_modules.cc_request import CamcopsRequest


class FhirExportException(Exception):
    pass


class FhirTaskExporter(object):
    """
    Class that knows how to export a single task to FHIR.
    """
    def __init__(self,
                 request: "CamcopsRequest",
                 exported_task_fhir: "ExportedTaskFhir") -> None:
        self.request = request
        self.exported_task = exported_task_fhir.exported_task
        self.exported_task_fhir = exported_task_fhir

        self.recipient = self.exported_task.recipient
        self.task = self.exported_task.task

        # TODO: In theory these settings should handle authentication
        # for any server that is SMART-compliant but we've not tested this.
        # https://sep.com/blog/smart-on-fhir-what-is-smart-what-is-fhir/
        settings = {
            "app_id": "camcops",
            "api_base": self.recipient.fhir_api_url,
            "app_secret": self.recipient.fhir_app_secret,
            "launch_token": self.recipient.fhir_launch_token,
        }

        try:
            self.client = client.FHIRClient(settings=settings)
        except Exception as e:
            raise FhirExportException(str(e))

    def export_task(self) -> None:
        """
        Export a single task to the server, with associated patient information
        if the task has an associated patient.
        """
        # TODO: Server capability statement
        # https://www.hl7.org/fhir/capabilitystatement.html

        # statement = self.client.server.capabilityStatement
        # The client doesn't support looking for a particular capability
        # We could check for:
        # fhirVersion (the client does not support multiple versions)
        # conditional create
        # supported resource types (statement.rest[0].resource[])
        bundle_entries = []

        if self.task.has_patient:
            patient_entry = self.task.patient.get_fhir_bundle_entry(
                self.request,
                self.exported_task.recipient
            )
            bundle_entries.append(patient_entry)

        try:
            task_entries = self.task.get_fhir_bundle_entries(
                self.request,
                self.exported_task.recipient
            )
            bundle_entries += task_entries

        except NotImplementedError as e:
            raise FhirExportException(str(e))

        bundle = Bundle(jsondict={
            "type": "transaction",
            "entry": bundle_entries,
        })

        try:
            # Attempt to create the receiver on the server, via POST:
            response = bundle.create(self.client.server)
            if response is None:
                # Not sure this will ever happen.
                # fhirabstractresource.py create() says it returns
                # "None or the response JSON on success" but an exception will
                # already have been raised if there was a failure
                raise FhirExportException(
                    "The server unexpectedly returned an OK, empty response")

            self.parse_response(response)
        except HTTPError as e:
            raise FhirExportException(
                f"The server returned an error: {e.response.text}")

        except Exception as e:
            # Unfortunate that fhirclient doesn't give us anything more
            # specific
            raise FhirExportException(e)

    def parse_response(self, response: Dict) -> None:
        """
        Parse the response from the FHIR server to which we have sent our
        task. The response looks something like this:

        .. code-block:: json

            {
              'resourceType': 'Bundle',
              'id': 'cae48957-e7e6-4649-97f8-0a882076ad0a',
              'type': 'transaction-response',
              'link': [
                {
                  'relation': 'self',
                  'url': 'http://localhost:8080/fhir'
                }
              ],
              'entry': [
                {
                  'response': {
                    'status': '200 OK',
                    'location': 'Patient/1/_history/1',
                    'etag': '1'
                  }
                },
                {
                  'response': {
                    'status': '200 OK',
                    'location': 'Questionnaire/26/_history/1',
                    'etag': '1'
                  }
                },
                {
                  'response': {
                    'status': '201 Created',
                    'location': 'QuestionnaireResponse/42/_history/1',
                    'etag': '1',
                    'lastModified': '2021-05-24T09:30:11.098+00:00'
                  }
                }
              ]
            }

        The server's reply contains a Bundle
        (https://www.hl7.org/fhir/bundle.html), which is a container for
        resources. Here, the bundle contains entry objects
        (https://www.hl7.org/fhir/bundle-definitions.html#Bundle.entry).

        """
        bundle = Bundle(jsondict=response)

        if bundle.entry is not None:
            self._save_exported_entries(bundle)

    def _save_exported_entries(self, bundle: Bundle) -> None:
        """
        Record the server's reply components in strucured format.
        """
        from camcops_server.cc_modules.cc_exportmodels import (
            ExportedTaskFhirEntry
        )
        for entry in bundle.entry:
            saved_entry = ExportedTaskFhirEntry()
            saved_entry.exported_task_fhir_id = self.exported_task_fhir.id
            saved_entry.status = entry.response.status
            saved_entry.location = entry.response.location
            saved_entry.etag = entry.response.etag
            if entry.response.lastModified is not None:
                # ... of type :class:`fhirclient.models.fhirdate.FHIRDate
                saved_entry.last_modified = entry.response.lastModified.date

            self.request.dbsession.add(saved_entry)
