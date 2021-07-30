# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - 监控平台 (BlueKing - Monitor) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import gettext as gettext_module
import importlib
import os

from django.apps import apps
from django.conf import settings
from django.utils import six
from django.utils._os import upath
from django.utils.translation import check_for_language, get_language
from django.views.i18n import render_javascript_catalog


def to_locale(language):
    """Turn a language name (en-us) into a locale name (en_US)."""
    language = language.lower()
    parts = language.split("-")
    try:
        country = parts[1]
    except IndexError:
        return language
    # A language with > 2 characters after the dash only has its first
    # character after the dash capitalized; e.g. sr-latn becomes sr_Latn.
    # A language with 2 characters after the dash has both characters
    # capitalized; e.g. en-us becomes en_US.
    parts[1] = country.title() if len(country) > 2 else country.upper()
    return parts[0] + "_" + "-".join(parts[1:])


def javascript_catalog(request, domain="djangojs", packages=None):
    """
    Returns the selected language catalog as a javascript library.

    Receives the list of packages to check for translations in the
    packages parameter either from an infodict or as a +-delimited
    string from the request. Default is 'django.conf'.

    Additionally you can override the gettext domain for this view,
    but usually you don't want to do that, as JavaScript messages
    go to the djangojs domain. But this might be needed if you
    deliver your JavaScript source from Django templates.
    """
    locale = to_locale(get_language())

    if request.GET and "language" in request.GET:
        if check_for_language(request.GET["language"]):
            locale = to_locale(request.GET["language"])

    if packages is None:
        packages = ["django.conf"]
    if isinstance(packages, six.string_types):
        packages = packages.split("+")

    catalog, plural = get_javascript_catalog(locale, domain, packages)
    return render_javascript_catalog(catalog, plural)


def get_javascript_catalog(locale, domain, packages):
    default_locale = to_locale(settings.LANGUAGE_CODE)
    app_configs = apps.get_app_configs()
    allowable_packages = {app_config.name for app_config in app_configs}
    allowable_packages.add("django.conf")
    packages = [p for p in packages if p in allowable_packages]
    t = {}
    paths = []
    # paths of requested packages
    for package in packages:
        p = importlib.import_module(package)
        path = os.path.join(os.path.dirname(upath(p.__file__)), "locale")
        paths.append(path)
    # add the filesystem paths listed in the LOCALE_PATHS setting
    paths.extend(list(reversed(settings.LOCALE_PATHS)))

    # first load the settings.LANGUAGE_CODE translations if it isn't english
    for path in paths:
        try:
            catalog = gettext_module.translation(domain, path, [default_locale])
        except IOError:
            catalog = None
        if catalog is not None:
            t.update(catalog._catalog)

    # next load the currently selected language,
    # if it isn't identical to the default.
    if locale != default_locale:
        locale_t = {}
        for path in paths:
            try:
                catalog = gettext_module.translation(domain, path, [locale])
            except IOError:
                catalog = None
            if catalog is not None:
                locale_t.update(catalog._catalog)
        if locale_t:
            t = locale_t
    plural = None
    if "" in t:
        for l in t[""].split("\n"):
            if l.startswith("Plural-Forms:"):
                plural = l.split(":", 1)[1].strip()
    if plural is not None:
        # this should actually be a compiled function of a typical plural-form:
        # Plural-Forms: nplurals=3; plural=n%10==1 && n%100!=11 ? 0 :
        #               n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2;
        plural = [el.strip() for el in plural.split(";") if el.strip().startswith("plural=")][0].split("=", 1)[1]

    pdict = {}
    maxcnts = {}
    catalog = {}
    for k, v in list(t.items()):
        if k == "":
            continue
        if isinstance(k, six.string_types):
            catalog[k] = v
        elif isinstance(k, tuple):
            msgid = k[0]
            cnt = k[1]
            maxcnts[msgid] = max(cnt, maxcnts.get(msgid, 0))
            pdict.setdefault(msgid, {})[cnt] = v
        else:
            raise TypeError(k)
    for k, v in list(pdict.items()):
        catalog[k] = [v.get(i, "") for i in range(maxcnts[msgid] + 1)]

    return catalog, plural
