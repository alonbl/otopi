#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""Utilities and tools."""


import gettext
import imp
import sys


__all__ = ['export']


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


def export(o):
    """Decoration to export module symbol.

    Usage:
        import util
        @util.export
        def x():
            pass

    """
    sys.modules[o.__module__].__dict__.setdefault(
        '__all__', []
    ).append(o.__name__)
    return o


@export
def codegen(o):
    """Decoration to code generate class symbols.

    Usage:
        import util
        @util.codegen
        class x():
            CONSTANT = 'value'

    """
    sys.modules[o.__module__].__dict__.setdefault(
        '__codegen__', []
    ).append(o)
    return o


@export
def methodsByAttribute(clz, attribute):
    """Query metadata information for specific method attribute.

    Keyword arguments:
    clz -- class to check.
    attribute -- attribute to find within methods.

    Returns:
        [attribute]


    Usable for class members decoration query.
    """
    ret = []
    for m in clz.__dict__.values():
        if hasattr(m, attribute):
            ret.append(getattr(m, attribute))
    return ret


@export
def raiseExceptionInformation(info):
    """Python-2/Python-3 raise exception based on exception information."""
    if hasattr(info[1], 'with_traceback'):
        raise info[1].with_traceback(info[2])
    else:
        exec('raise info[1], None, info[2]')


@export
def loadModule(path, name):
    """Dynamic load module.

    Keyword arguments:
    path -- path to load from.
    name -- name of module.

    Returns:
    Loaded module.

    """
    mod_fobj, mod_absp, mod_desc = imp.find_module(
        name.split('.')[-1],
        [path]
    )
    try:
        return imp.load_module(
            name,
            mod_fobj,
            mod_absp,
            mod_desc
        )
    finally:
        if mod_fobj is not None:
            mod_fobj.close()


# vim: expandtab tabstop=4 shiftwidth=4
