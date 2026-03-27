REQUEST_COUNT: dict[str, int] = {"n": 0}


def inc_request() -> None:
    REQUEST_COUNT["n"] = REQUEST_COUNT.get("n", 0) + 1
