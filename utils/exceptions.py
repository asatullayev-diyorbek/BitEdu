from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return Response(
            {
                "status": response.status_code,
                "message": "Error",
                "data": response.data,
            },
            status=response.status_code,
        )

    return Response(
        {
            "status": 500,
            "message": "Internal server error",
            "data": None,
        },
        status=500,
    )
