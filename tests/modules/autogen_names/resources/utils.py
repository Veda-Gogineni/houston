# -*- coding: utf-8 -*-
"""
Autogenerated_names resources utils
-------------
"""
import tests.modules.site_settings.resources.utils as setting_utils


def create_autogen_name(
    flask_app_client, user, data, expected_status_code=200, expected_error=''
):
    existing_data = read_all_autogen_names(flask_app_client, user)
    existing_data.update(data)
    setting_utils.modify_main_settings(
        flask_app_client,
        user,
        {'_value': existing_data},
        'autogenerated_names',
        expected_status_code=expected_status_code,
        expected_error=expected_error,
    )


def read_all_autogen_names(flask_app_client, user, expected_status_code=200):
    block_data = setting_utils.read_main_settings(
        flask_app_client,
        user,
        expected_status_code=expected_status_code,
    ).json
    if expected_status_code == 200:
        return setting_utils.extract_from_main_block(block_data, 'autogenerated_names')