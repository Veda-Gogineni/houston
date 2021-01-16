# -*- coding: utf-8 -*-

from tests.extensions.config import utils


def test_set_db_config(flask_app, db):
    from app.extensions.config import HoustonFlaskConfig

    try:
        assert flask_app.config['ENV'] == 'production'
        utils._get_and_check_houston_configs()  # Ensure an empty database of existing configs

        # Check that the context is setup correctly on launch
        assert isinstance(flask_app.config, HoustonFlaskConfig)
        utils._check_outside_db_context(flask_app)

        # First, check (current_app) environment is setup and torn down correctly by context
        with flask_app.config.db():
            utils._check_inside_db_context(flask_app)

        # Check that the context properly exited
        utils._check_outside_db_context(flask_app)

        # Second, check if a specific app environment works correclt
        with flask_app.config.db(flask_app):
            utils._check_inside_db_context(flask_app, db_app=flask_app)

        # Check that the context properly exited
        utils._check_outside_db_context(flask_app)

        new_env = 'testing-no-db'

        # Update config without a database context
        flask_app.config['ENV'] = new_env
        assert flask_app.config['ENV'] == new_env

        # Ensure that there are still no existing configs in the database
        utils._get_and_check_houston_configs()

        new_env = 'testing-with-db'

        # Update with database
        with flask_app.config.db(flask_app):
            utils._check_inside_db_context(flask_app, db_app=flask_app)
            flask_app.config['ENV'] = new_env

        # Check that the value has updated in the Flask config
        utils._check_outside_db_context(flask_app)
        assert flask_app.config['ENV'] == new_env

        # Check that the value has updated in the database
        utils._get_and_check_houston_configs(key='ENV', value=new_env)
    finally:
        flask_app.config['ENV'] = 'production'
        utils._delete_all_houston_configs(db)


def test_forget_db_config(flask_app, db):
    # Ensure this config is empty and ENV is the value 'production'
    assert flask_app.config['ENV'] == 'production'
    utils._get_and_check_houston_configs()  # Ensure an empty database of existing configs

    new_env = 'testing-with-db'

    # Update with database
    with flask_app.config.db(flask_app):
        utils._check_inside_db_context(flask_app, db_app=flask_app)
        flask_app.config['ENV'] = new_env

    # Check that the value has updated in the Flask config
    utils._check_outside_db_context(flask_app)
    assert flask_app.config['ENV'] == new_env

    # Check that the value has updated in the database
    utils._get_and_check_houston_configs(key='ENV', value=new_env)

    # Delete (by forgetting) the database value override for this configuration
    flask_app.config.forget('ENV')

    # Ensure that the value has been deleted from the database
    utils._delete_all_houston_configs(db)
