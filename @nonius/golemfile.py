#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def configure(project):

    project.dependency(name='boost',
                       targets=["boost_system"],
                       repository='https://github.com/boostorg/boost.git',
                       version='~1.69.0',
                       variant='release',
                       shallow=True)

    project.export(name='nonius',
                   includes=['include'],
                   header_only=True,
                   licenses=['COPYING.txt'],
                   deps=['boost'])
