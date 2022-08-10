# -*- coding: utf-8 -*-
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
import datetime
import functools
import json
import logging
import time

import pytz
import requests
import werkzeug.exceptions
from flask import current_app, request, session
from flask_login import current_user

log = logging.getLogger(__name__)


def create_session_oauth2_client(user, **kwargs):
    from app.extensions import db
    from app.extensions.api import api_v1
    from app.modules.auth.models import OAuth2Client

    default_scopes = list(api_v1.authorizations['oauth2_password']['scopes'].keys())

    # Retrieve Oauth2 client for user and/or clean-up multiple clients
    session_oauth2_clients = OAuth2Client.query.filter_by(
        user=user, level=OAuth2Client.ClientLevels.session, **kwargs
    ).all()
    session_oauth2_client = None
    if len(session_oauth2_clients) == 1:
        # We have an existing Oauth2 frontend client for this user, let's re-use it
        session_oauth2_client = session_oauth2_clients[0]
    elif len(session_oauth2_clients) > 1:
        # We have somehow created multiple clients for this user, delete them all and make new ones
        with db.session.begin():
            for session_oauth2_client_ in session_oauth2_clients:
                db.session.delete(session_oauth2_client_)

    if session_oauth2_client is None:
        session_oauth2_client = OAuth2Client(
            level=OAuth2Client.ClientLevels.session,
            user=user,
            default_scopes=default_scopes,
            **kwargs,
        )
        with db.session.begin():
            db.session.add(session_oauth2_client)
    log.debug('Using session Oauth2 client = {!r}'.format(session_oauth2_client))
    return session_oauth2_client


def create_session_oauth2_token(
    cleanup_tokens=False, check_renewal=False, user=None, update_session=True
):
    from app.extensions import db
    from app.extensions.api import api_v1
    from app.modules.auth.models import OAuth2Token

    default_scopes = list(api_v1.authorizations['oauth2_password']['scopes'].keys())

    if user is None:
        user = current_user
        if not user.is_authenticated:
            return None

    session_oauth2_client = create_session_oauth2_client(user)

    # Clean-up all tokens for the confidential client
    session_oauth2_bearer_tokens = OAuth2Token.query.filter_by(
        client=session_oauth2_client
    ).all()
    log.info(
        'User %s has %d confidential Oauth2 bearer tokens'
        % (
            user.email,
            len(session_oauth2_bearer_tokens),
        )
    )
    if cleanup_tokens:
        for session_oauth2_bearer_token_ in session_oauth2_bearer_tokens:
            log.info(
                'Cleaning up User %s Oauth2 bearer token: %r'
                % (
                    user.email,
                    len(session_oauth2_bearer_tokens),
                )
            )
            session_oauth2_bearer_token_.delete()

    # IMPORTANT: WE NEED THIS TO BE IN UTC FOR OAUTH2
    expires = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(days=1)

    # Create a Oauth2 session bearer token with all scopes for this session
    session_oauth2_bearer_token = OAuth2Token(
        client=session_oauth2_client,
        user=user,
        token_type='Bearer',
        scopes=default_scopes,
        expires=expires,
    )
    with db.session.begin():
        db.session.add(session_oauth2_bearer_token)

    # Add the access token to the session

    if update_session:
        session_oauth2_access_token = session_oauth2_bearer_token.access_token
        session['access_token'] = session_oauth2_access_token

    return session_oauth2_bearer_token


def check_session_oauth2_token(autorenew=True, user=None):
    from app.modules.auth.models import OAuth2Token

    if user is None:
        user = current_user

    if not user.is_authenticated:
        return False

    session_oauth2_access_token = session.get('access_token', None)
    if session_oauth2_access_token is None:
        return False

    session_oauth2_bearer_token = OAuth2Token.find(
        access_token=session_oauth2_access_token
    )
    if session_oauth2_bearer_token is None:
        if autorenew:
            create_session_oauth2_token()
            return True
        else:
            return False

    if session_oauth2_bearer_token.is_expired:
        if autorenew:
            create_session_oauth2_token()
            return True
        else:
            return False

    return None


def delete_session_oauth2_token(user=None):
    from app.modules.auth.models import OAuth2Token

    if user is None:
        user = current_user

    session_oauth2_access_token = session.get('access_token', None)
    if session_oauth2_access_token is not None:
        session_oauth2_bearer_token = OAuth2Token.find(
            access_token=session_oauth2_access_token
        )
        log.info(
            'Deleting bearer token %r for user %r'
            % (session_oauth2_bearer_token, user.email),
        )
        if session_oauth2_bearer_token is not None:
            session_oauth2_bearer_token.delete()


def recaptcha_required(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        from app.modules.site_settings.models import SiteSetting

        if not SiteSetting.get_value('recaptchaPublicKey'):
            log.debug('Recaptcha skipped (recaptchaPublicKey not set)')
            return func(*args, **kwargs)

        token = json.loads(request.data).get('token')

        if token == current_app.config.get('RECAPTCHA_BYPASS'):
            return func(*args, **kwargs)

        # Retry 10 times if there's an error
        for i in range(10):
            try:
                response = requests.post(
                    current_app.config.get('RECAPTCHA_SITE_VERIFY_API'),
                    data={
                        'secret': SiteSetting.get_value('recaptchaSecretKey'),
                        'response': token,
                    },
                ).json()
                break
            except requests.exceptions.ConnectionError:
                response = {}
                time.sleep(2)
            except requests.exceptions.RequestException:
                response = {}
                log.exception('Recaptcha failure')

        log.debug(f'Recaptcha response={response}')
        score = response.get('score', 0)
        success = response.get('success', False)

        if not success:
            # Probably misconfigured or API changed
            log.error(f'Recaptcha response failure: {response}')
            raise werkzeug.exceptions.BadRequest(
                f'Recaptcha response failure: {response}'
            )
        if score >= 0.5:
            return func(*args, **kwargs)

        log.error(f'Recaptcha bot score failed: {response}')
        raise werkzeug.exceptions.BadRequest('Recaptcha bot score failed')

    return inner
