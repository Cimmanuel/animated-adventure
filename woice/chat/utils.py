import re


def strip_str(str, format_as):
    """
    Removes unnecessary whitespaces from given `str`
    Args:
        str: string to be formatted
        format_as: [
            type of formatting to be done. takes either `url`
            or `normal`. use `url` to format URLs and `normal`
            to do normal string formatting
        ]
    """
    stripped_str = ""

    if format_as == "url":
        stripped_str = re.sub(" +", "", str)
    elif format_as == "normal":
        stripped_str = re.sub(" +", " ", str)

    return stripped_str
