# -*- coding: utf-8 -*-
#
# Copyright 2013 - Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Access Control API server."""

from keystonemiddleware import auth_token
from oslo_config import cfg
from oslo_policy import policy

from mistral import exceptions as exc


_ENFORCER = None


def setup(app):
    if cfg.CONF.pecan.auth_enable:
        conf = dict(cfg.CONF.keystone_authtoken)

        # Change auth decisions of requests to the app itself.
        conf.update({'delay_auth_decision': True})
        _ensure_enforcer_initialization()

        return auth_token.AuthProtocol(app, conf)
    else:
        return app


def enforce(action, context, target=None, do_raise=True,
            exc=exc.NotAllowedException):
    target_obj = {
        'project_id': context.project_id,
        'user_id': context.user_id,
    }

    target_obj.update(target or {})
    _ensure_enforcer_initialization()

    return _ENFORCER.enforce(
        action,
        target_obj,
        context.to_dict(),
        do_raise=do_raise,
        exc=exc
    )


def _ensure_enforcer_initialization():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(cfg.CONF)
        _ENFORCER.load_rules()


def get_limited_to(headers):
    """Return the user and project the request should be limited to.

    :param headers: HTTP headers dictionary
    :return: A tuple of (user, project), set to None if there's no limit on
    one of these.

    """
    return headers.get('X-User-Id'), headers.get('X-Project-Id')


def get_limited_to_project(headers):
    """Return the project the request should be limited to.

    :param headers: HTTP headers dictionary
    :return: A project, or None if there's no limit on it.

    """
    return get_limited_to(headers)[1]
