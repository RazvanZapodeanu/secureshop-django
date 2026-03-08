from django import template
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import random

register = template.Library()


@register.simple_tag
def produs_zilei():
    produs = cache.get('produs_zilei')
    
    if not produs:
        from products.models import Produs
        produse = Produs.objects.filter(disponibil=True, stoc__gt=0)
        if produse.exists():
            produs = random.choice(list(produse))
            now = timezone.now()
            midnight = now.replace(hour=23, minute=59, second=59)
            timeout = (midnight - now).seconds
            cache.set('produs_zilei', produs, timeout)
    
    if produs:
        html = f'''
        <div class="produs-zilei-banner">
            <h3>⭐ PRODUSUL ZILEI ⭐</h3>
            <p class="produs-zilei-nume">{produs.nume}</p>
            <p class="produs-zilei-pret">{produs.pret} LEI</p>
            <a href="/produs/{produs.slug}/" class="produs-zilei-btn">Vezi Detalii</a>
        </div>
        '''
        return mark_safe(html)
    return ''


@register.simple_tag(takes_context=True)
def pret_euro(context, pret):
    curs = settings.CURS_EUR
    pret_eur = round(float(pret) / curs, 2)
    
    html = f'''
    <span class="pret-container">
        <span class="pret-ron">Pret: {pret} RON</span>
        <span class="pret-eur">({pret_eur} EUR)</span>
    </span>
    '''
    return mark_safe(html)


@register.inclusion_tag('products/ultimele_vizualizari.html', takes_context=True)
def ultimele_vizualizari(context):
    request = context.get('request')
    vizualizari = []
    
    if request and request.user.is_authenticated:
        from products.models import Vizualizare
        today = timezone.now().date()
        
        viz = Vizualizare.objects.filter(
            utilizator=request.user,
            data_vizualizare__date=today
        ).select_related('produs').order_by('-data_vizualizare')[:settings.VIZ_PROD]
        
        seen = set()
        for v in viz:
            if v.produs.id not in seen:
                vizualizari.append(v.produs)
                seen.add(v.produs.id)
    
    return {'vizualizari': vizualizari}


@register.filter
def pret_in_euro(value):
    try:
        return round(float(value) / settings.CURS_EUR, 2)
    except (ValueError, TypeError):
        return value
