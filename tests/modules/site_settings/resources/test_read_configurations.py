# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
from tests.modules.site_settings.resources import utils as conf_utils
import pytest

from tests.utils import module_unavailable, extension_unavailable


@pytest.mark.skipif(extension_unavailable('edm'), reason='EDM extension disabled')
@pytest.mark.skipif(
    module_unavailable('site_settings'), reason='Site-settings module disabled'
)
def test_read_site_settings(flask_app_client, researcher_1):
    # pylint: disable=invalid-name
    test_key = 'site.name'
    response = conf_utils.read_main_settings(flask_app_client, researcher_1, test_key)
    assert response.json['response']['id'] == test_key
    response = conf_utils.read_main_settings_definition(
        flask_app_client, researcher_1, test_key
    )
    assert response.json['response']['configurationId'] == test_key
    assert response.json['response']['fieldType'] == 'string'

    # a bad key
    response = conf_utils.read_main_settings(
        flask_app_client, researcher_1, '__INVALID_KEY__', expected_status_code=400
    )

    from app.modules.ia_config_reader import IaConfig

    ia_config_reader = IaConfig()
    species = ia_config_reader.get_configured_species()
    config_def_response = conf_utils.read_main_settings_definition(
        flask_app_client, researcher_1, 'site.species'
    )
    # note: this relies on IaConfig and get_configured_species() not changing too radically
    assert len(config_def_response.json['response']['suggestedValues']) >= len(species)
    for i in range(len(species)):
        assert (
            config_def_response.json['response']['suggestedValues'][i]['scientificName']
            == species[len(species) - i - 1]
        )

    config_def_response = conf_utils.read_main_settings_definition(
        flask_app_client, researcher_1
    )
    assert len(
        config_def_response.json['response']['configuration']['site.species'][
            'suggestedValues'
        ]
    ) >= len(species)
    for i in range(len(species)):
        assert (
            config_def_response.json['response']['configuration']['site.species'][
                'suggestedValues'
            ][i]['scientificName']
            == species[len(species) - i - 1]
        )

    # test private (will give 403 to non-admin)
    response = conf_utils.read_main_settings(
        flask_app_client, researcher_1, 'site.testSecret', expected_status_code=403
    )


@pytest.mark.skipif(extension_unavailable('edm'), reason='EDM extension disabled')
@pytest.mark.skipif(
    module_unavailable('site_settings'), reason='Site-settings module disabled'
)
def test_alter_settings(flask_app_client, admin_user):
    response = conf_utils.read_main_settings(flask_app_client, admin_user, 'site.species')
    assert 'value' in response.json['response']
    vals = response.json['response']['value']
    vals.append({'commonNames': ['Test data'], 'scientificName': 'Testus datum'})
    response = conf_utils.modify_main_settings(
        flask_app_client,
        admin_user,
        {'_value': vals},
        'site.species',
    )
    response = conf_utils.read_main_settings(flask_app_client, admin_user, 'site.species')
    assert 'value' in response.json['response']
    assert response.json['response']['value'][-1]['scientificName'] == 'Testus datum'
    # restore original list
    vals.pop()
    response = conf_utils.modify_main_settings(
        flask_app_client,
        admin_user,
        {'_value': vals},
        'site.species',
    )


def test_dict_write(flask_app_client, admin_user):
    # Create json site setting
    data = {
        'Matriarch': {'multipleInGroup': False},
        'IrritatingGit': {'multipleInGroup': True},
    }

    resp = conf_utils.modify_main_settings(
        flask_app_client, admin_user, data, 'social_group_roles'
    )

    assert resp.json['key'] == 'social_group_roles'

    conf_utils.delete_main_setting(flask_app_client, admin_user, 'social_group_roles')