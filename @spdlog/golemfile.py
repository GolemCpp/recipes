def configure(project):

    project.export(
        name="spdlog", includes=["include"], header_only=True, licenses=["LICENSE"]
    )
