class MissingContextVariableError(Exception):
    """
    Raised when template field cannot be rendered because variable used in it is not present in the context.
    """
    def __init__(self, field_name, variable):
        super().__init__(
            'Cannot render field "{}", because variable "{}" is not defined in the context.'.format(
                field_name, variable
            )
        )
