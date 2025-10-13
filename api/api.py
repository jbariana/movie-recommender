def handle_button_click(button_id):
    # Hard-coded mapping
    mapping = {
        "view_ratings_button": "View Ratings Button handled",
        "view_statistics_button": "View Statistics Button handled",
        "get_rec_button": "Get Recommendations Button handled",
        "add_rating_button": "Add Rating Button handled",
        "remove_rating_button": "Remove Rating Button handled"
    }
    return {"button": mapping.get(button_id, "Unknown Button")}