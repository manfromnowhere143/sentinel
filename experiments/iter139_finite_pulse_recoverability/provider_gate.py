"""Pure pre-connection check for completed provider start and instance identity."""


def require_ready(operation, instance):
    identity = "3834622546652649531"
    zone = "https://www.googleapis.com/compute/v1/projects/sunlit-unison-487018-b0/zones/us-west1-a"
    if (
        operation.get("status") != "DONE"
        or "error" in operation
        or "httpErrorStatusCode" in operation
        or operation.get("operationType") != "start"
        or operation.get("targetId") != identity
        or operation.get("zone") != zone
    ):
        raise ValueError("successful completed start operation required")
    if (
        instance.get("id") != identity
        or instance.get("status") != "RUNNING"
        or instance.get("zone") != zone
        or instance.get("machineType") != zone + "/machineTypes/g2-standard-8"
    ):
        raise ValueError("running original instance required")
