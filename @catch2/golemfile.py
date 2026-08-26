#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def configure(project):

    project.export(name='catch',
                   includes=['single_include'],
                   header_only=True,
                   licenses=['LICENSE.txt'])
