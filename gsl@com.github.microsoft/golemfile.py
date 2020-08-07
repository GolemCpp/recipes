#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def configure(project):

    project.export(name='gsl',
                   includes=['include'],
                   header_only=True,
                   licenses=['LICENSE', 'ThirdPartyNotices.txt'])
