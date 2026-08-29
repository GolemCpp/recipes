def configure(project):

    project.dependency(name='boost',
                       targets=["boost_system"],
                       location='@boost',
                       version='*',
                       variant='release',
                       shallow=True)

    project.export(name='nonius',
                   includes=['include'],
                   header_only=True,
                   licenses=['COPYING.txt'],
                   deps=['boost'])
