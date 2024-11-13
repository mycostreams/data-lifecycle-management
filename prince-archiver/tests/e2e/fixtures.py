import httpx


def client(context):
    with httpx.Client() as client:
        context.client = client
        yield context.client


def get_exports(context):
    def _get_exports():
        client: httpx.Client = context.client
        response = client.get(f"http://localhost:8002/api/1/exports")
        assert response.status_code == 200
        return response.json()

    context.get_exports = _get_exports

    yield _get_exports
