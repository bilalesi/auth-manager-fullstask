from enum import Enum, auto

from fastapi import status


class AutoStringEnum(str, Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.lower()


class ErrorKeys(AutoStringEnum):
    internal_error = auto()
    keycloak_error = auto()
    keycloak_callback_error = auto()
    unauthorized = auto()
    token_not_active = auto()
    token_not_found = auto()
    validation_error = auto()
    invalid_request = auto()
    invalid_ack_state = auto()
    database_error = auto()


errors_mapping = {
    ErrorKeys.keycloak_error: status.HTTP_502_BAD_GATEWAY,
    ErrorKeys.keycloak_callback_error: status.HTTP_502_BAD_GATEWAY,
    ErrorKeys.unauthorized: status.HTTP_401_UNAUTHORIZED,
    ErrorKeys.token_not_active: status.HTTP_401_UNAUTHORIZED,
    ErrorKeys.token_not_found: status.HTTP_404_NOT_FOUND,
    ErrorKeys.validation_error: status.HTTP_400_BAD_REQUEST,
    ErrorKeys.invalid_request: status.HTTP_400_BAD_REQUEST,
    ErrorKeys.invalid_ack_state: status.HTTP_400_BAD_REQUEST,
    ErrorKeys.internal_error: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorKeys.database_error: status.HTTP_502_BAD_GATEWAY,
}
