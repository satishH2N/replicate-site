import os
import azure.functions as func

async def main(req: func.HttpRequest) -> func.HttpResponse:
    path = req.route_params.get('path')
    file_path = os.path.join(os.path.dirname(__file__), '..', 'jp-connect-site-utils', 'static', path)

    if not os.path.isfile(file_path):
        return func.HttpResponse("File not found", status_code=404)

    with open(file_path, 'rb') as file:
        file_content = file.read()

    content_type = "text/plain"
    if file_path.endswith(".css"):
        content_type = "text/css"
    elif file_path.endswith(".js"):
        content_type = "application/javascript"
    elif file_path.endswith(".html"):
        content_type = "text/html"

    return func.HttpResponse(file_content, mimetype=content_type)
