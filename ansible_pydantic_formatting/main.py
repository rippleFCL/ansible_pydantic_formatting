from pydantic import ValidationError, BaseModel
from typing import Any, Sequence, overload
from ansible.errors import AnsibleLookupError


def parse_errors(e: ValidationError, name: str, var_name: str) -> str:
    schema_errors = []
    for error in e.errors():
        print(error)
        loc = (name, *error["loc"]) if name else error["loc"]
        path = f"{var_name}"
        for _, pos in enumerate(loc):  # skip last
            if isinstance(pos, str):
                path += f".{pos}"
            elif isinstance(pos, int):
                path += f"[{pos}]"
            else:
                raise TypeError("Unexpected type")
        schema_errors.append(f"{error['msg'].lower()} at {path}")
    raise AnsibleLookupError(f"schema errors: {', '.join(schema_errors)}")


@overload
def validate_model[T: type[BaseModel]](model: T, data: Sequence[Any], var_name: str) -> list[T]: ...

@overload
def validate_model[T: type[BaseModel]](model: T, data: dict[str, Any], var_name: str) -> dict[str, T]: ...

def validate_model[T: type[BaseModel]](
    model: T, data: dict[str, Any] | Sequence[Any], var_name: str
) -> dict[str, T] | list[T]:
    name = ""
    try:
        if isinstance(data, dict):
            validated_dict: dict[str, T] = {}
            for name, value in data.items():
                validated_dict[name] = model.model_validate(value)
            return validated_dict
        elif isinstance(data, list):
            validated_list: list[T] = []
            for value in data:
                validated_list.append(model.model_validate(value))
            return validated_list
    except ValidationError as e:
        parse_errors(e, name, var_name)

    raise ValueError("Unexpected type")

