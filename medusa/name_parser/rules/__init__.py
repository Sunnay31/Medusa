#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Guessit customization."""
from guessit.api import default_api
from ...name_parser.rules.properties import (
    blacklist, container, format_, other,
    screen_size
)
from ...name_parser.rules.rules import rules


default_api.rebulk.rebulk(blacklist())
default_api.rebulk.rebulk(format_())
default_api.rebulk.rebulk(screen_size())
default_api.rebulk.rebulk(other())
default_api.rebulk.rebulk(container())
default_api.rebulk.rebulk(rules())
