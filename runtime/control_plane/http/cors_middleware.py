from aiohttp import web


def admin_control_plane_cors_middleware(
    *,
    allowed_origins: set[str],
):
    @web.middleware
    async def _middleware(request: web.Request, handler):
        origin = request.headers.get("Origin")

        # Handle preflight
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            response = await handler(request)

        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type"
            )

        return response

    return _middleware
