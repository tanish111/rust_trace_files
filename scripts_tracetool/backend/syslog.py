# -*- coding: utf-8 -*-

"""
Syslog built-in backend.
"""

__author__     = "Paul Durrant <paul.durrant@citrix.com>"
__copyright__  = "Copyright 2016, Citrix Systems Inc."
__license__    = "GPL version 2 or (at your option) any later version"

__maintainer__ = "Stefan Hajnoczi"
__email__      = "stefanha@redhat.com"


import os.path
import re
from tracetool import out


PUBLIC = True
import re

# Macro expansions simulate the suffixes from <inttypes.h>
macro_expansions = {
    "PRIx64": "lx",
    "PRIx32": "x",
    "PRIu64": "lu",
    "PRIu32": "u",
    "PRId64": "ld",
    "PRId32": "d",
    "PRIi64": "li",
    "PRIi32": "i",
}

# Updated regex to match ALL valid C printf-style format specifiers
C_FORMAT_SPECIFIER_REGEX = re.compile(
    r"%(?:\d+\$)?[+\-0# ]*\d*(?:\.\d+)?(?:hh|h|ll|l|j|z|t|L)?[diuoxXfFeEgGaAcspn%]"
)

def c_format_to_rust_format(c_expr: str) -> str:
    """
    Converts C-style format strings (possibly split across macros) to Rust-style format strings.
    E.g.:
        '"cpu=%d pc=0x%" PRIx64 " flags=0x%x"'
        \u2192 'cpu={} pc=0x{:x} flags=0x{}'
    """

    # Tokenize input: quoted strings and bare identifiers/macros
    tokens = re.findall(r'"[^"]*"|\w+', c_expr)

    # Step 1: join tokens into single format string (simulate C preprocessor)
    collapsed = ""
    for tok in tokens:
        if tok.startswith('"') and tok.endswith('"'):
            collapsed += tok[1:-1]  # remove quotes
        elif tok in macro_expansions:
            collapsed += macro_expansions[tok]  # do not prefix %
        else:
            collapsed += tok

    # Step 2: Replace C-style format specifiers with Rust-style ones
    def convert(match):
        spec = match.group(0)
        if spec == "%%":
            return "%"
        elif spec[-1] in "xX":
            return "{:x}"
        else:
            return "{:?}"

    return C_FORMAT_SPECIFIER_REGEX.sub(convert, collapsed)

def generate_h_begin(events, group):
    out('#include <syslog.h>',
        '')


def generate_h(event, group):
    argnames = ", ".join(event.args.names())
    if len(event.args) > 0:
        argnames = ", " + argnames

    out('#line %(event_lineno)d "%(event_filename)s"',
        '        syslog(LOG_INFO, "%(name)s " %(fmt)s %(argnames)s);',
        '#line %(out_next_lineno)d "%(out_filename)s"',
        event_lineno=event.lineno,
        event_filename=os.path.relpath(event.filename),
        name=event.name,
        fmt=event.fmt.rstrip("\n"),
        argnames=argnames)

def generate_rs(event, group):
    out('let formatted_msg = format!(%(fmt)s, %(args)s);',
        'let c_msg = CString::new(formatted_msg).unwrap();',
        'unsafe {syslog(LOG_INFO, c_msg.as_ptr());}',
        name=event.name,
        fmt="\""+c_format_to_rust_format(event.fmt.rstrip("\n"))+"\"",
        args=", ".join(f"_{name}" for name in event.args.names()))

def generate_h_backend_dstate(event, group):
    out('    trace_event_get_state_dynamic_by_id(%(event_id)s) || \\',
        event_id="TRACE_" + event.name.upper())
