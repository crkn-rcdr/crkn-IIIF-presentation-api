def get_slug_in_metadata(metadata:list) ->list:
    """
    Retrieves the value corresponding to the label 'Slug' from a list of metadata items.
    """
    for item in metadata:
        for key,value in item["label"].items():
            if value[0].lower() == "slug":
                return list(item["value"].values())[0]
    return None
