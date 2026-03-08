from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.mail import send_mail, mail_admins, send_mass_mail
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Count
from .models import Produs, Discount, Specificatie, Review, Categorie, Utilizator, Vizualizare, Promotie, Comanda, ProdusComanda, Nota, IncercareLagare
from datetime import datetime, date, timedelta
from collections import Counter
from decimal import Decimal
import json
import os
import time
import re
import secrets
import logging

logger = logging.getLogger('django')

visits_list = []

class Accesare:
    next_id = 1
    def __init__(self, ip_client, full_url, timestamp):
        self.id = Accesare.next_id
        Accesare.next_id += 1
        self.ip_client = ip_client
        self.full_url = full_url
        self.timestamp = timestamp
    
    def lista_parametri(self):
        if '?' not in self.full_url:
            return []
        query_string = self.full_url.split('?')[1]
        params = []
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params.append((key, value))
            else:
                params.append((param, None))
        return params
    
    def url(self):
        return self.full_url
    
    def data(self, format_string):
        return self.timestamp.strftime(format_string)
    
    def pagina(self):
        path = self.full_url
        if '?' in path:
            path = path.split('?')[0]
        if '://' in path:
            path = path.split('://')[1]
            path = path.split('/', 1)[1]
        return '/' + path


def afis_data(show_type):
    now = datetime.now()
    days = ['Luni', 'Marti', 'Miercuri', 'Joi', 'Vineri', 'Sambata', 'Duminica']
    months = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie', 'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']
    day_name = days[now.weekday()]
    day_number = now.day
    month_name = months[now.month - 1]
    year = now.year
    time_str = now.strftime('%H:%M:%S')
    full_date = f"{day_name}, {day_number} {month_name} {year}"
    
    html_part = "<section><h2>Data si ora</h2>"
    if show_type == 'zi':
        html_part += f"<p>{full_date}</p>"
    elif show_type == 'timp':
        html_part += f"<p>{time_str}</p>"
    else:
        html_part += f"<p>{full_date}, {time_str}</p>"
    html_part += "</section>"
    return html_part


def index(request):
    logger.info('Pagina principala accesata')
    produs_zilei = cache.get('produs_zilei')
    if not produs_zilei:
        produse = Produs.objects.filter(disponibil=True, stoc__gt=0)
        if produse.exists():
            import random
            produs_zilei = random.choice(list(produse))
            now = timezone.now()
            midnight = now.replace(hour=23, minute=59, second=59)
            timeout = (midnight - now).seconds
            cache.set('produs_zilei', produs_zilei, timeout)
    
    return render(request, 'products/index.html', {'produs_zilei': produs_zilei})


def despre(request):
    return render(request, 'products/about.html')


def produse(request):
    from .forms import FiltruProduseForm
    logger.debug('Filtrare produse initiata')
    
    form = FiltruProduseForm(request.GET or None)
    lista_produse = Produs.objects.all()
    
    mesaj_paginare = None
    produse_pe_pagina_anterioare = request.session.get('produse_pe_pagina', 6)
    
    produse_pe_pagina_cache = cache.get(f'produse_pe_pagina_{request.user.id}' if request.user.is_authenticated else 'produse_pe_pagina_anon')
    if produse_pe_pagina_cache:
        form.fields['produse_pe_pagina'].initial = produse_pe_pagina_cache
    
    if form.is_valid():
        if form.cleaned_data.get('nume'):
            lista_produse = lista_produse.filter(nume__icontains=form.cleaned_data['nume'])
        if form.cleaned_data.get('producator'):
            lista_produse = lista_produse.filter(producator=form.cleaned_data['producator'])
        if form.cleaned_data.get('categorie'):
            lista_produse = lista_produse.filter(categorii=form.cleaned_data['categorie'])
        if form.cleaned_data.get('tag'):
            lista_produse = lista_produse.filter(tag_uri=form.cleaned_data['tag'])
        if form.cleaned_data.get('pret_min') is not None:
            lista_produse = lista_produse.filter(pret__gte=form.cleaned_data['pret_min'])
        if form.cleaned_data.get('pret_max') is not None:
            lista_produse = lista_produse.filter(pret__lte=form.cleaned_data['pret_max'])
        if form.cleaned_data.get('stoc_min') is not None:
            lista_produse = lista_produse.filter(stoc__gte=form.cleaned_data['stoc_min'])
        if form.cleaned_data.get('stoc_max') is not None:
            lista_produse = lista_produse.filter(stoc__lte=form.cleaned_data['stoc_max'])
        if form.cleaned_data.get('cod_produs'):
            lista_produse = lista_produse.filter(cod_produs__icontains=form.cleaned_data['cod_produs'])
        disponibil_val = form.cleaned_data.get('disponibil')
        if disponibil_val in ['True', 'False']:
            lista_produse = lista_produse.filter(disponibil=(disponibil_val == 'True'))
        
        produse_pe_pagina_noua = form.cleaned_data.get('produse_pe_pagina') or 6
        if produse_pe_pagina_noua != produse_pe_pagina_anterioare:
            mesaj_paginare = f"Ai schimbat paginarea de la {produse_pe_pagina_anterioare} la {produse_pe_pagina_noua} produse per pagina. Este posibil sa fi sarit peste unele produse sau sa vezi din nou produse deja vizualizate."
            request.session['produse_pe_pagina'] = produse_pe_pagina_noua
            cache_key = f'produse_pe_pagina_{request.user.id}' if request.user.is_authenticated else 'produse_pe_pagina_anon'
            cache.set(cache_key, produse_pe_pagina_noua, 60*60*24*5)
    else:
        produse_pe_pagina_noua = produse_pe_pagina_cache or 6
    
    sort_param = request.GET.get('sort')
    if sort_param == 'a':
        lista_produse = lista_produse.order_by('pret')
    elif sort_param == 'd':
        lista_produse = lista_produse.order_by('-pret')
    
    disponibile = []
    indisponibile = []
    
    for produs in lista_produse:
        discount_activ = Discount.objects.filter(
            produs=produs, activ=True,
            data_inceput__lte=timezone.now(),
            data_sfarsit__gte=timezone.now()
        ).first()
        
        if discount_activ:
            procent_decimal = Decimal(str(discount_activ.procent)) / Decimal('100')
            pret_final = produs.pret * (Decimal('1') - procent_decimal)
            produs.pret_cu_discount = round(pret_final, 2)
            produs.discount_activ = discount_activ
        else:
            produs.pret_cu_discount = produs.pret
            produs.discount_activ = None
        
        if produs.stoc > 0:
            disponibile.append(produs)
        else:
            indisponibile.append(produs)
    
    produse_cu_discount = disponibile + indisponibile
    
    produse_pe_pag = form.cleaned_data.get('produse_pe_pagina') if form.is_valid() else (produse_pe_pagina_cache or 6)
    if not produse_pe_pag:
        produse_pe_pag = 6
    
    paginator = Paginator(produse_cu_discount, produse_pe_pag)
    nr_pagina = request.GET.get('pagina')
    mesaj_eroare = None
    
    try:
        pagina_curenta = paginator.page(nr_pagina)
    except PageNotAnInteger:
        pagina_curenta = paginator.page(1)
    except EmptyPage:
        pagina_curenta = paginator.page(paginator.num_pages)
        mesaj_eroare = "Nu mai sunt produse pe aceasta pagina"
    
    context = {
        'pagina': pagina_curenta,
        'eroare': mesaj_eroare,
        'form': form,
        'mesaj_paginare': mesaj_paginare,
        'este_pagina_categorie': False
    }
    
    return render(request, 'products/produse.html', context)


def contact(request):
    from .forms import ContactForm
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            
            data_nasterii = data['data_nasterii']
            today = date.today()
            ani = today.year - data_nasterii.year - ((today.month, today.day) < (data_nasterii.month, data_nasterii.day))
            if today.month >= data_nasterii.month:
                luni = today.month - data_nasterii.month
            else:
                luni = 12 + today.month - data_nasterii.month
                ani -= 1
            data['varsta'] = f"{ani} de ani si {luni} luni"
            del data['data_nasterii']
            del data['confirmare_email']
            
            mesaj = data['mesaj']
            mesaj = mesaj.replace('\n', ' ').replace('\r', ' ')
            mesaj = re.sub(r'\s+', ' ', mesaj)
            mesaj = re.sub(r'([.?!…]\s+)([a-zăâîșț])', lambda m: m.group(1) + m.group(2).upper(), mesaj)
            data['mesaj'] = mesaj
            
            tip_mesaj = data['tip_mesaj']
            zile = data['minim_zile_asteptare']
            minim_necesar = {'review': 4, 'cerere': 4, 'intrebare': 2, 'reclamatie': 0, 'programare': 0}
            urgent = (zile == minim_necesar.get(tip_mesaj, 0))
            data['urgent'] = urgent
            
            data['ip_client'] = request.META.get('REMOTE_ADDR', 'unknown')
            data['data_sosire'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
            mesaje_dir = os.path.join(os.path.dirname(__file__), 'Mesaje')
            os.makedirs(mesaje_dir, exist_ok=True)
            
            timestamp = int(time.time())
            nume_fisier = f"mesaj_{timestamp}"
            if urgent:
                nume_fisier += "_urgent"
            nume_fisier += ".json"
            
            cale_fisier = os.path.join(mesaje_dir, nume_fisier)
            with open(cale_fisier, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            messages.success(request, 'Mesajul a fost trimis cu succes!')
            logger.info(f'Mesaj contact primit de la {data.get("email")}')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'products/contact.html', {'form': form})


def cos_virtual(request):
    return render(request, 'products/cos_virtual.html')


def adauga_produs(request):
    if not request.user.has_perm('products.add_produs'):
        request.session['erori_403'] = request.session.get('erori_403', 0) + 1
        return render(request, 'products/403.html', {
            'titlu': 'Eroare adaugare produse',
            'mesaj_personalizat': 'Nu ai voie sa adaugi produse de securitate!',
            'numar_erori': request.session.get('erori_403', 1)
        }, status=403)
    
    from .forms import AdaugaProdusForm
    
    if request.method == 'POST':
        form = AdaugaProdusForm(request.POST, request.FILES)
        if form.is_valid():
            produs = form.save()
            messages.success(request, f'Produsul "{produs.nume}" a fost adaugat cu succes!')
            logger.info(f'Produs nou adaugat: {produs.nume} de catre {request.user.username}')
            return redirect('detaliu_produs', slug=produs.slug)
    else:
        form = AdaugaProdusForm()
    
    return render(request, 'products/adauga_produs.html', {'form': form})


def info(request):
    if request.user.is_authenticated and not request.user.groups.filter(name='Administratori_site').exists() and not request.user.is_superuser:
        request.session['erori_403'] = request.session.get('erori_403', 0) + 1
        return render(request, 'products/403.html', {
            'titlu': 'Acces interzis',
            'mesaj_personalizat': 'Aceasta pagina este disponibila doar pentru administratorii site-ului.',
            'numar_erori': request.session.get('erori_403', 1)
        }, status=403)
    
    params = request.GET
    numar_parametri = len(params)
    nume_parametri = ", ".join(params.keys()) if params else "Niciunul"
    
    sectiune_data = ""
    data_param = request.GET.get('data')
    if data_param:
        sectiune_data = afis_data(data_param)
    
    context = {
        'sectiune_data': sectiune_data,
        'numar_parametri': numar_parametri,
        'nume_parametri': nume_parametri,
    }
    return render(request, 'products/info.html', context)


def log(request):
    if request.user.is_authenticated and not request.user.groups.filter(name='Administratori_site').exists() and not request.user.is_superuser:
        request.session['erori_403'] = request.session.get('erori_403', 0) + 1
        return render(request, 'products/403.html', {
            'titlu': 'Acces interzis',
            'mesaj_personalizat': 'Aceasta pagina este disponibila doar pentru administratorii site-ului.',
            'numar_erori': request.session.get('erori_403', 1)
        }, status=403)
    
    html = "<h1>Jurnal Accesari</h1>"
    visits_to_show = visits_list.copy()
    eroare = None
    
    ultimele = request.GET.get('ultimele')
    if ultimele:
        try:
            n = int(ultimele)
            if n > len(visits_list):
                eroare = f"Exista doar {len(visits_list)} accesari fata de {n} accesari cerute"
            visits_to_show = visits_list[-n:]
        except ValueError:
            eroare = "Parametrul 'ultimele' trebuie sa fie un numar intreg"
            visits_to_show = []
    
    iduri_param = request.GET.getlist('iduri')
    dubluri = request.GET.get('dubluri', 'false').lower() == 'true'
    
    if iduri_param:
        all_ids = []
        for id_string in iduri_param:
            for id_val in id_string.split(','):
                try:
                    all_ids.append(int(id_val.strip()))
                except ValueError:
                    pass
        
        seen = set()
        visits_to_show = []
        for id_val in all_ids:
            if not dubluri and id_val in seen:
                continue
            seen.add(id_val)
            for visit in visits_list:
                if visit.id == id_val:
                    visits_to_show.append(visit)
                    break
    
    accesari_param = request.GET.get('accesari')
    if accesari_param == 'nr':
        html += f"<section><h2>Numar total accesari</h2><p>{len(visits_list)} accesari de la pornirea serverului</p></section>"
    elif accesari_param == 'detalii':
        html += "<section><h2>Detalii accesari</h2><ul>"
        for visit in visits_to_show:
            html += f"<li>{visit.data('%d/%m/%Y %H:%M:%S')}</li>"
        html += "</ul></section>"
    
    tabel_param = request.GET.get('tabel')
    sql_param = request.GET.get('sql')
    
    if tabel_param:
        if tabel_param == 'tot':
            cols = ['id', 'ip_client', 'url', 'data']
        else:
            cols = [c.strip() for c in tabel_param.split(',')]
        
        html += "<table style='width:100%; border-collapse:collapse; margin:20px 0;'>"
        html += "<thead><tr style='background:#1A1A2E;'>"
        for col in cols:
            html += f"<th style='padding:12px; border:1px solid #00D9FF; color:#00D9FF;'>{col.upper()}</th>"
        html += "</tr></thead><tbody>"
        
        for visit in visits_to_show:
            html += "<tr>"
            for col in cols:
                if col == 'id':
                    html += f"<td style='padding:8px; border:1px solid #ddd;'>{visit.id}</td>"
                elif col == 'ip_client':
                    html += f"<td style='padding:8px; border:1px solid #ddd;'>{visit.ip_client}</td>"
                elif col == 'url':
                    html += f"<td style='padding:8px; border:1px solid #ddd;'>{visit.url()}</td>"
                elif col == 'data':
                    html += f"<td style='padding:8px; border:1px solid #ddd;'>{visit.data('%d/%m/%Y %H:%M:%S')}</td>"
                else:
                    html += f"<td style='padding:8px; border:1px solid #ddd;'>-</td>"
            html += "</tr>"
        
        html += "</tbody></table>"
    else:
        for visit in visits_to_show:
            html += f"<p>ID: {visit.id} | Pagina: {visit.pagina()} | IP: {visit.ip_client} | Data: {visit.data('%d/%m/%Y %H:%M:%S')}</p>"
    
    if sql_param == 'true':
        from django.db import connection
        queries = connection.queries
        html += "<section><h2>Comenzi SQL</h2>"
        html += f"<p>Numar total comenzi: {len(queries)}</p>"
        html += "<ul>"
        for q in queries:
            html += f"<li>{q['sql'][:100]}... ({q['time']}s)</li>"
        html += "</ul></section>"
    
    if not visits_to_show:
        html += "<p>Nu exista accesari de afisat.</p>"
    
    if eroare:
        html += f"<p style='color:red;'>{eroare}</p>"
    
    if visits_list:
        pages = [visit.pagina() for visit in visits_list]
        counter = Counter(pages)
        if counter:
            most_accessed = counter.most_common(1)[0]
            least_accessed = counter.most_common()[-1]
            html += "<hr><div style='display:flex; justify-content:space-between; margin:30px 0;'>"
            html += "<div style='flex:1; margin:0 10px; padding:20px; background:#00D9FF; color:#0F0F1E; border-radius:10px; text-align:center;'>"
            html += "<h3>CEL MAI MULT ACCESATA</h3>"
            html += f"<p style='font-size:24px; font-weight:bold;'>{most_accessed[0]}</p>"
            html += f"<small>({most_accessed[1]} accesari)</small></div>"
            html += "<div style='flex:1; margin:0 10px; padding:20px; background:#FB7E14; color:#0F0F1E; border-radius:10px; text-align:center;'>"
            html += "<h3>CEL MAI PUTIN ACCESATA</h3>"
            html += f"<p style='font-size:24px; font-weight:bold;'>{least_accessed[0]}</p>"
            html += f"<small>({least_accessed[1]} accesari)</small></div></div>"
    
    return render(request, 'products/log.html', {'log_html': html})


def detaliu_produs(request, slug):
    try:
        produs = Produs.objects.get(slug=slug)
    except Produs.DoesNotExist:
        logger.warning(f'Produs inexistent accesat: {slug}')
        return render(request, 'products/404_produs.html', status=404)
    
    if request.user.is_authenticated:
        vizualizari = Vizualizare.objects.filter(utilizator=request.user).order_by('-data_vizualizare')
        if vizualizari.count() >= settings.MAX_VIZUALIZARI:
            vizualizari.last().delete()
        Vizualizare.objects.create(utilizator=request.user, produs=produs)
    
    discount_activ = Discount.objects.filter(
        produs=produs, activ=True,
        data_inceput__lte=timezone.now(),
        data_sfarsit__gte=timezone.now()
    ).first()
    
    pret_final = produs.pret
    if discount_activ:
        procent_decimal = Decimal(str(discount_activ.procent)) / Decimal('100')
        pret_final = produs.pret * (Decimal('1') - procent_decimal)
        pret_final = round(pret_final, 2)
    
    specificatii = produs.specificatii.filter(activa=True).order_by('ordine')
    reviews = produs.review.all()[:5]
    
    rating_mediu = None
    if reviews.exists():
        total_rating = sum([r.rating for r in reviews])
        rating_mediu = round(total_rating / reviews.count(), 1)
    
    context = {
        'produs': produs,
        'discount_activ': discount_activ,
        'pret_final': pret_final,
        'specificatii': specificatii,
        'reviews': reviews,
        'rating_mediu': rating_mediu,
    }
    
    return render(request, 'products/detaliu_produs.html', context)


def categorie(request, slug):
    try:
        categorie = Categorie.objects.get(slug=slug, activa=True)
    except Categorie.DoesNotExist:
        raise Http404("Categoria nu exista")
    
    from .forms import FiltruProduseForm
    form = FiltruProduseForm(request.GET or None, categorie_fixa=categorie.id)
    lista_produse = Produs.objects.filter(categorii=categorie)
    
    mesaj_paginare = None
    produse_pe_pagina_anterioare = request.session.get('produse_pe_pagina', 4)
    
    if form.is_valid():
        if form.cleaned_data.get('nume'):
            lista_produse = lista_produse.filter(nume__icontains=form.cleaned_data['nume'])
        if form.cleaned_data.get('producator'):
            lista_produse = lista_produse.filter(producator=form.cleaned_data['producator'])
        if form.cleaned_data.get('tag'):
            lista_produse = lista_produse.filter(tag_uri=form.cleaned_data['tag'])
        if form.cleaned_data.get('pret_min') is not None:
            lista_produse = lista_produse.filter(pret__gte=form.cleaned_data['pret_min'])
        if form.cleaned_data.get('pret_max') is not None:
            lista_produse = lista_produse.filter(pret__lte=form.cleaned_data['pret_max'])
        if form.cleaned_data.get('stoc_min') is not None:
            lista_produse = lista_produse.filter(stoc__gte=form.cleaned_data['stoc_min'])
        if form.cleaned_data.get('stoc_max') is not None:
            lista_produse = lista_produse.filter(stoc__lte=form.cleaned_data['stoc_max'])
        if form.cleaned_data.get('cod_produs'):
            lista_produse = lista_produse.filter(cod_produs__icontains=form.cleaned_data['cod_produs'])
        if form.cleaned_data.get('disponibil'):
            disponibil_bool = form.cleaned_data['disponibil'] == 'True'
            lista_produse = lista_produse.filter(disponibil=disponibil_bool)
        
        produse_pe_pagina_noua = form.cleaned_data.get('produse_pe_pagina') or 4
        if produse_pe_pagina_noua != produse_pe_pagina_anterioare:
            mesaj_paginare = f"Ai schimbat paginarea de la {produse_pe_pagina_anterioare} la {produse_pe_pagina_noua} produse per pagina."
            request.session['produse_pe_pagina'] = produse_pe_pagina_noua
    else:
        produse_pe_pagina_noua = 4
    
    sort_param = request.GET.get('sort')
    if sort_param == 'a':
        lista_produse = lista_produse.order_by('pret')
    elif sort_param == 'd':
        lista_produse = lista_produse.order_by('-pret')
    
    disponibile = []
    indisponibile = []
    
    for produs in lista_produse:
        discount_activ = Discount.objects.filter(
            produs=produs, activ=True,
            data_inceput__lte=timezone.now(),
            data_sfarsit__gte=timezone.now()
        ).first()
        
        if discount_activ:
            procent_decimal = Decimal(str(discount_activ.procent)) / Decimal('100')
            pret_final = produs.pret * (Decimal('1') - procent_decimal)
            produs.pret_cu_discount = round(pret_final, 2)
            produs.discount_activ = discount_activ
        else:
            produs.pret_cu_discount = produs.pret
            produs.discount_activ = None
        
        if produs.stoc > 0:
            disponibile.append(produs)
        else:
            indisponibile.append(produs)
    
    produse_cu_discount = disponibile + indisponibile
    
    produse_pe_pag = form.cleaned_data.get('produse_pe_pagina') if form.is_valid() else 4
    if not produse_pe_pag:
        produse_pe_pag = 4
    
    paginator = Paginator(produse_cu_discount, produse_pe_pag)
    nr_pagina = request.GET.get('pagina')
    mesaj_eroare = None
    
    try:
        pagina_curenta = paginator.page(nr_pagina)
    except PageNotAnInteger:
        pagina_curenta = paginator.page(1)
    except EmptyPage:
        pagina_curenta = paginator.page(paginator.num_pages)
        mesaj_eroare = "Nu mai sunt produse pe aceasta pagina"
    
    context = {
        'pagina': pagina_curenta,
        'eroare': mesaj_eroare,
        'categorie': categorie,
        'form': form,
        'mesaj_paginare': mesaj_paginare,
        'este_pagina_categorie': True
    }
    
    return render(request, 'products/produse.html', context)


def inregistrare(request):
    from .forms import InregistrareForm
    
    if request.method == 'POST':
        form = InregistrareForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.email_confirmat = False
            user.cod = secrets.token_urlsafe(50)
            user.save()
            
            link_confirmare = request.build_absolute_uri(f'/confirma_mail/{user.cod}/')
            
            html_message = render_to_string('products/email_confirmare.html', {
                'user': user,
                'link_confirmare': link_confirmare,
            })
            
            send_mail(
                'Bun venit pe Secured Systems!',
                strip_tags(html_message),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=True
            )
            
            messages.success(request, 'Te-ai inregistrat cu succes! Verifica-ti emailul pentru a confirma contul.')
            logger.info(f'Utilizator nou inregistrat: {user.username}')
            return redirect('login')
    else:
        form = InregistrareForm()
    
    return render(request, 'products/inregistrare.html', {'form': form})


def confirma_mail(request, cod):
    try:
        user = Utilizator.objects.get(cod=cod)
        user.email_confirmat = True
        user.cod = None
        user.save()
        messages.success(request, 'Email-ul a fost confirmat cu succes! Te poti loga acum.')
        logger.info(f'Email confirmat pentru: {user.username}')
    except Utilizator.DoesNotExist:
        messages.error(request, 'Link invalid sau expirat.')
        logger.warning(f'Incercare de confirmare email cu cod invalid: {cod}')
    
    return redirect('login')


def login_view(request):
    from .forms import LoginForm
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        username = request.POST.get('username')
        ip = request.META.get('REMOTE_ADDR')
        
        if form.is_valid():
            user = form.get_user()
            
            if form.cleaned_data.get('remember_me'):
                request.session.set_expiry(86400)
            else:
                request.session.set_expiry(0)
            
            login(request, user)
            
            request.session['user_data'] = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telefon': user.telefon,
                'adresa': user.adresa,
                'oras': user.oras,
                'judet': user.judet,
            }
            
            messages.success(request, f'Bun venit, {user.first_name or user.username}!')
            logger.info(f'Login reusit: {user.username}')
            return redirect('profil')
        else:
            IncercareLagare.objects.create(username=username, ip_address=ip)
            
            recent = timezone.now() - timedelta(minutes=2)
            incercari = IncercareLagare.objects.filter(username=username, ip_address=ip, data_incercare__gte=recent).count()
            
            if incercari >= 3:
                mail_admins(
                    'Logari suspecte',
                    f'S-au detectat {incercari} incercari de logare esuate pentru username: {username} de la IP: {ip}',
                    html_message=f'<h1 style="color:red;">Logari suspecte</h1><p>Username: {username}</p><p>IP: {ip}</p><p>Incercari: {incercari}</p>'
                )
                logger.critical(f'Logari suspecte detectate: {username} de la {ip}')
    else:
        form = LoginForm()
    
    return render(request, 'products/login.html', {'form': form})


@login_required
def logout_view(request):
    perm = Permission.objects.filter(codename='vizualizeaza_oferta').first()
    if perm and request.user.has_perm('products.vizualizeaza_oferta'):
        request.user.user_permissions.remove(perm)
    
    logout(request)
    messages.info(request, 'Te-ai delogat cu succes!')
    return redirect('index')


@login_required
def profil(request):
    cache_key = f'profil_{request.user.id}'
    profil_data = cache.get(cache_key)
    
    if not profil_data:
        user_data = request.session.get('user_data', {})
        profil_data = user_data
        cache.set(cache_key, profil_data, 60*60*24*5)
    
    campuri_lipsa = []
    campuri_importante = ['telefon', 'adresa']
    
    for camp in ['telefon', 'adresa', 'oras', 'judet', 'cod_postal']:
        if not getattr(request.user, camp):
            campuri_lipsa.append(camp)
    
    if campuri_lipsa:
        messages.warning(request, f'Ai campuri necompletate in profil: {", ".join(campuri_lipsa)}')
    
    return render(request, 'products/profil.html', {'user_data': profil_data, 'campuri_lipsa': campuri_lipsa})


@login_required
def schimba_parola(request):
    from .forms import SchimbaParolaForm
    
    if request.method == 'POST':
        form = SchimbaParolaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Parola a fost schimbata cu succes!')
            logger.info(f'Parola schimbata pentru: {user.username}')
            return redirect('profil')
    else:
        form = SchimbaParolaForm(request.user)
    
    return render(request, 'products/schimba_parola.html', {'form': form})


@login_required
def editare_profil(request):
    from .forms import EditareProfilForm
    
    if request.method == 'POST':
        form = EditareProfilForm(request.POST, instance=request.user)
        
        date_initiale = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'telefon': request.user.telefon,
            'adresa': request.user.adresa,
            'oras': request.user.oras,
            'judet': request.user.judet,
            'cod_postal': request.user.cod_postal,
        }
        
        if form.is_valid():
            date_noi = form.cleaned_data
            modificari = False
            
            for camp, valoare in date_noi.items():
                if str(valoare) != str(date_initiale.get(camp, '')):
                    modificari = True
                    break
            
            if not modificari:
                messages.info(request, 'Nu ai facut nicio modificare.')
            else:
                form.save()
                cache.delete(f'profil_{request.user.id}')
                messages.success(request, 'Profilul a fost actualizat cu succes!')
                logger.info(f'Profil actualizat: {request.user.username}')
            
            return redirect('profil')
    else:
        form = EditareProfilForm(instance=request.user)
    
    campuri_lipsa = []
    for camp in ['telefon', 'adresa', 'oras', 'judet', 'cod_postal']:
        if not getattr(request.user, camp):
            campuri_lipsa.append(camp)
    
    if campuri_lipsa:
        messages.error(request, f'<ul>{"".join([f"<li>{c}</li>" for c in campuri_lipsa])}</ul>')
    
    return render(request, 'products/editare_profil.html', {'form': form})


@login_required
def promotii(request):
    from .forms import PromotieForm
    
    if request.method == 'POST':
        form = PromotieForm(request.POST)
        if form.is_valid():
            promotie = form.save()
            
            categorii_selectate = form.cleaned_data['categorii']
            
            messages_to_send = []
            
            for categorie in categorii_selectate:
                utilizatori = Utilizator.objects.filter(
                    vizualizari__produs__categorii=categorie
                ).annotate(
                    nr_viz=Count('vizualizari')
                ).filter(nr_viz__gte=settings.MIN_VIZUALIZARI_PROMOTIE)
                
                for user in utilizatori:
                    mesaj = f"Promotie {promotie.nume} pentru categoria {categorie.nume}! Reducere {promotie.procent_reducere}% pana la {promotie.data_expirare.strftime('%d/%m/%Y')}"
                    messages_to_send.append((
                        f'Promotie: {promotie.nume}',
                        mesaj,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email]
                    ))
            
            if messages_to_send:
                send_mass_mail(messages_to_send, fail_silently=True)
            
            messages.success(request, 'Promotia a fost creata si email-urile au fost trimise!')
            return redirect('promotii')
    else:
        form = PromotieForm()
    
    return render(request, 'products/promotii.html', {'form': form})


def oferta(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if not request.user.has_perm('products.vizualizeaza_oferta'):
        request.session['erori_403'] = request.session.get('erori_403', 0) + 1
        return render(request, 'products/403.html', {
            'titlu': 'Eroare afisare oferta',
            'mesaj_personalizat': 'Nu ai voie sa vizualizezi oferta.',
            'numar_erori': request.session.get('erori_403', 1)
        }, status=403)
    
    return render(request, 'products/oferta.html')


@login_required
def acorda_oferta(request):
    perm = Permission.objects.get(codename='vizualizeaza_oferta')
    request.user.user_permissions.add(perm)
    messages.success(request, 'Felicitari! Ai acces la oferta speciala!')
    return redirect('oferta')


@login_required
def cumpara(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            produse = data.get('produse', [])
            
            if not produse:
                return JsonResponse({'error': 'Cosul este gol'}, status=400)
            
            comanda = Comanda.objects.create(
                utilizator=request.user,
                adresa_livrare=request.user.adresa or 'Adresa nespecificata',
                total=0
            )
            
            total = Decimal('0')
            
            for item in produse:
                produs = Produs.objects.get(id=item['id'])
                cantitate = item['cantitate']
                
                if produs.stoc < cantitate:
                    return JsonResponse({'error': f'Stoc insuficient pentru {produs.nume}'}, status=400)
                
                produs.stoc -= cantitate
                produs.save()
                
                ProdusComanda.objects.create(
                    comanda=comanda,
                    produs=produs,
                    cantitate=cantitate,
                    pret_unitar=produs.pret
                )
                
                total += produs.pret * cantitate
            
            comanda.total = total
            comanda.save()
            
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            facturi_dir = os.path.join(settings.MEDIA_ROOT, 'temporar-facturi', request.user.username)
            os.makedirs(facturi_dir, exist_ok=True)
            
            timestamp = int(time.time())
            pdf_path = os.path.join(facturi_dir, f'factura-{timestamp}.pdf')
            
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph(f'<b>FACTURA #{comanda.id}</b>', styles['Title']))
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(f'Client: {request.user.get_full_name() or request.user.username}', styles['Normal']))
            elements.append(Paragraph(f'Email: {request.user.email}', styles['Normal']))
            elements.append(Paragraph(f'Data: {comanda.data_comanda.strftime("%d/%m/%Y %H:%M")}', styles['Normal']))
            elements.append(Spacer(1, 20))
            
            data_table = [['Produs', 'Cantitate', 'Pret unitar', 'Subtotal']]
            for pc in comanda.produse_comanda.all():
                data_table.append([
                    pc.produs.nume,
                    str(pc.cantitate),
                    f'{pc.pret_unitar} LEI',
                    f'{pc.subtotal} LEI'
                ])
            data_table.append(['', '', 'TOTAL:', f'{comanda.total} LEI'])
            
            table = Table(data_table)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00D9FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FB7E14')),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(f'Contact administrator: {settings.ADMINS[0][1] if settings.ADMINS else "admin@example.com"}', styles['Normal']))
            
            doc.build(elements)
            
            with open(pdf_path, 'rb') as f:
                send_mail(
                    f'Factura comanda #{comanda.id}',
                    'Multumim pentru comanda! Gasiti factura atasata.',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=True
                )
            
            logger.info(f'Comanda #{comanda.id} plasata de {request.user.username}')
            return JsonResponse({'success': True, 'comanda_id': comanda.id})
            
        except Exception as e:
            logger.error(f'Eroare la plasarea comenzii: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Metoda invalida'}, status=405)


def nota_produs(request, produs_id, nota):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if nota < 1 or nota > 5:
        messages.error(request, 'Nota trebuie sa fie intre 1 si 5.')
        return redirect('index')
    
    try:
        produs = Produs.objects.get(id=produs_id)
    except Produs.DoesNotExist:
        messages.error(request, 'Produsul nu exista.')
        return redirect('index')
    
    existing = Nota.objects.filter(utilizator=request.user, produs=produs).exists()
    if existing:
        messages.info(request, 'Ai acordat deja o nota acestui produs.')
        return redirect('detaliu_produs', slug=produs.slug)
    
    Nota.objects.create(utilizator=request.user, produs=produs, nota=nota)
    messages.success(request, f'Ai acordat {nota} stele produsului {produs.nume}!')
    
    return redirect('detaliu_produs', slug=produs.slug)


def interzis(request):
    request.session['erori_403'] = request.session.get('erori_403', 0) + 1
    return render(request, 'products/403.html', {
        'titlu': 'Eroare 403',
        'mesaj_personalizat': 'Nu aveti permisiunea de a accesa aceasta resursa.',
        'numar_erori': request.session.get('erori_403', 1)
    }, status=403)

def finalizeaza_comanda(request):
    return render(request, 'products/in_lucru.html')