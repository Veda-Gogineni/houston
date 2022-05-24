# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import logging
from tests import utils as test_utils
import pytest
from tests.utils import module_unavailable


log = logging.getLogger(__name__)


@pytest.mark.skipif(module_unavailable('sightings'), reason='Sightings module disabled')
def test_clear_up_empty_sightings(flask_app_client, researcher_1, admin_user):

    # shouldn't be allowed
    test_utils.post_via_flask(
        flask_app_client,
        researcher_1,
        scopes='sightings:write',
        path='/api/v1/sightings/remove_all_empty',
        data={},
        expected_status_code=403,
        response_200={},
    )
    # should be allowed
    resp = test_utils.post_via_flask(
        flask_app_client,
        admin_user,
        scopes='sightings:write',
        path='/api/v1/sightings/remove_all_empty',
        data={},
        expected_status_code=None,
        response_200={},
    )
    assert resp.status_code == 200
