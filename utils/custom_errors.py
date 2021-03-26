class TokenError(Exception):
    pass


class ToManyRequestError(Exception):
    pass


class ValidationError(Exception):
    pass


class InvalidRequestError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


def handle_errors(resp):
    if resp.status_code == 401:
        raise TokenError(resp.json()['error'])
    if resp.status_code == 429:
        raise ToManyRequestError(resp.json()['error'])
    if resp.status_code == 400:
        raise InvalidRequestError(resp.json()['error'])
    if resp.status_code == 404:
        raise ResourceNotFoundError(resp.json()['error'])
