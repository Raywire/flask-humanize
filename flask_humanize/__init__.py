#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask_humanize.py
    ~~~~~~~~~~~~~~~~~

    Add common humanization utilities, like turning number into a fuzzy
    human-readable duration or into human-readable size, to your flask
    applications.

    :copyright: (c) by Vital Kudzelka
    :license: MIT
"""
import humanize
from flask import current_app
from werkzeug.datastructures import ImmutableDict

from . import compat


__version__ = '0.0.1'


def force_unicode(value):
    if not isinstance(value, compat.text_type):
        return value.decode('utf-8')
    return value


def app_has_babel(app):
    """Check application instance for configured babel extension."""
    obj = app.extensions.get('babel')
    return obj is not None


def self_name(string):
    """Create config key for extension."""
    return 'HUMANIZE_{}'.format(string.upper())


default_config = ImmutableDict({
    # The default locale to work with. When `BABEL_DEFAULT_LOCALE` is
    # available then it used instead.
    'default_locale': 'en',
})


class Humanize(object):
    """Add common humanization utilities, like turning number into a fuzzy
    human-readable duration or into human-readable size, to your flask
    applications.
    """

    # A function uses for locale selection.
    locale_selector_func = None

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize application to use with extension.

        :param app: The Flask instance.

        Example::

            from myapp import create_app()
            from flask_humanize import Humanize

            app = create_app()
            humanize.init_app(app)

        """
        for k, v in default_config.items():
            app.config.setdefault(self_name(k), v)

        if app_has_babel(app):
            default_locale = app.config['BABEL_DEFAULT_LOCALE']
            if default_locale is not None:
                app.config.setdefault(self_name('default_locale'), default_locale)

        app.add_template_filter(self.__humanize, 'humanize')
        app.before_request(self.__set_locale)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['humanize'] = self

    @property
    def default_locale(self):
        """Returns the default locale for current application."""
        return current_app.config['HUMANIZE_DEFAULT_LOCALE']

    def localeselector(self, func):
        """Registers a callback function for locale selection.

        Callback is a callable which returns the locale as string,
        e.g. ``'en_US'``, ``'ru_RU'``::

            from flask import request

            @humanize.localeselector
            def get_locale():
                return request.accept_languages.best_match(available_locales)

        When no callback is available or `None` is returned, then locale
        falls back to the default one from application configuration.
        """
        self.locale_selector_func = func
        return func

    def __set_locale(self):
        if self.locale_selector_func is None:
            locale = self.default_locale
        else:
            locale = self.locale_selector_func()
            if locale is None:
                locale = self.default_locale

        humanize.i18n.activate(locale)

    def __humanize(self, value, fname='naturaltime', **kwargs):
        try:
            method = getattr(humanize, fname)
        except AttributeError:
            raise Exception(
                "Humanize module does not contains function '%s'" % fname
            )

        try:
            value = method(value, **kwargs) if kwargs else method(value)
        except Exception:
            raise ValueError(
                "An error occured during execution function '%s'" % fname
            )

        return force_unicode(value)