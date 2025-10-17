from .views import Accesare, visits_list
from datetime import datetime

class MiddlewareVisits:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        access = Accesare(
            ip_client=request.META.get('REMOTE_ADDR'),
            full_url=request.build_absolute_uri(),
            timestamp=datetime.now()
        )
        visits_list.append(access)
        
        print(f"[MIDDLEWARE] Visit #{access.id}: {access.pagina()}")
        
        response = self.get_response(request)
        
        return response