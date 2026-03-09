from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")

        status_code = response.status_code if response else 200

        if isinstance(data, dict) and \
                {"status", "message", "data"} <= data.keys():
            return super().render(data, accepted_media_type, renderer_context)

        formatted_response = {
            "status": status_code,
            "message": "Success" if status_code < 400 else "Error",
            "data": data,
        }

        return super().render(
            formatted_response,
            accepted_media_type,
            renderer_context
        )
