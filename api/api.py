def handle_button_click(button_id):
    if button_id == "view_ratings_button":
        return "HELLOHELLOOOOO"
    elif button_id == "view_statistics_button":
        return "View Statistics Function Called"
    elif button_id == "get_rec_button":
        return "recommendation function called"
    elif button_id == "add_rating_button":
        return "Add Rating Function Called"
    elif button_id == "remove_rating_button":
        return "Remove Rating Function Called"
    else:
        return "Unknown Button"