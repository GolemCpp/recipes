def configure(project):

    project.export(name='catch',
                   includes=['single_include'],
                   header_only=True,
                   licenses=['LICENSE.txt'])
