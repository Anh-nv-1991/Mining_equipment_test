from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "error": {
                "status_code": response.status_code,
                "message": response.data.get("detail", "An error occurred"),
                "fields": {k: v for k, v in response.data.items() if k != "detail"}
            }
        }
    return response
