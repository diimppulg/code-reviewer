from flask import request

def render_comment():
    comment = request.args.get("comment", "")
    return f"<div>{comment}</div>"
