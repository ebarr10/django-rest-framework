from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    scope = "sustained"


class GetThrottle(UserRateThrottle):
    scope = "get_throttle"

    def allow_request(self, request, view):
        if request.method != "GET":
            return True
        return super().allow_request(request, view)


class PostThrottle(UserRateThrottle):
    scope = "post_throttle"

    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        return super().allow_request(request, view)
