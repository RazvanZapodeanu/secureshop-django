from datetime import datetime

class MiddlewareVisits:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .views import visits_list, Accesare
        
        full_url = request.build_absolute_uri()
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        timestamp = datetime.now()
        
        visit = Accesare(ip, full_url, timestamp)
        visits_list.append(visit)
        
        response = self.get_response(request)
        return response
