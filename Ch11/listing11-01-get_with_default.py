def get_item(variable, key, default=None):
    try:
        return variable[key]
    except (KeyError, IndexError):
        # Key is invalid for variable, the error raised depends on the type of variable
        return default
    except TypeError:
        if hasattr(variable, "__getitem__"):
            return default
        else:
            raise

