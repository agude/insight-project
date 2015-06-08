def tags_from_csv_field(tag_string):
    """Split a tag string and return a list of cleaned tags."""
    split_string = tag_string.split()
    out_list = []
    for tag in split_string:
        out_list.append(clean_tag(tag))

    return out_list


def clean_tag(tag):
    """ Clean up a single tag. """
    tmp0 = tag.strip()
    tmp1 = tmp0.lower()
    return tmp1
