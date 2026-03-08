from .models import Categorie
from django.conf import settings
from datetime import datetime

def categorii_menu(request):
    return {
        'categorii_menu': Categorie.objects.filter(activa=True)
    }


def relatii_clienti(request):
    zile_map = {
        0: 'luni',
        1: 'marti',
        2: 'miercuri',
        3: 'joi',
        4: 'vineri',
        5: 'sambata',
        6: 'duminica',
    }
    
    now = datetime.now()
    zi_curenta = zile_map[now.weekday()]
    ora_curenta = now.hour
    
    program = settings.PROGRAM_RELATII_CLIENTI.get(zi_curenta)
    
    if program is None:
        status = 'Serviciul "Relatii cu Clientii" este indisponibil la aceasta ora'
    elif program['start'] <= ora_curenta < program['end']:
        status = f'Puteti contacta azi departamentul "Relatii cu Clientii" pana la ora {program["end"]}:00'
    else:
        status = 'Serviciul "Relatii cu Clientii" este indisponibil la aceasta ora'
    
    return {
        'status_relatii_clienti': status
    }
