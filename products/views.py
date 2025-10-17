from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from collections import Counter
from .models import Produs,Discount
from django.utils import timezone
from decimal import Decimal

visits_list = []

class Accesare:
    next_id=1
    def __init__(self, ip_client, full_url, timestamp):
        self.id=Accesare.next_id
        Accesare.next_id+=1
        self.ip_client=ip_client
        self.full_url=full_url
        self.timestamp=timestamp
    
    def lista_parametri(self):
        if '?' not in self.full_url:
            return []
        
        query_string=self.full_url.split('?')[1]
        params=[]
        
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params.append((key,value))
            else:
                params.append((param, None))
        return params
    
    def url(self):
        return self.full_url
    
    def data(self ,format_string):
        return self.timestamp.strftime(format_string)
    
    def pagina(self):
        path=self.full_url
        if '?' in path:
            path=path.split('?')[0]
        path=path.split('://')[1]
        path=path.split('/',1)[1]
        return '/'+path
    
    
def show_data(show_type):
    now=datetime.now()
    days=['Luni','Marti','Miercuri','Joi','Vineri','Sambata','Duminica']
    months=['Ianuarie','Februarie','Martie','Aprilie','Mai','Iunie',
        'Iulie','August','Septembrie','Octombrie','Noiembrie','Decembrie']
    day_name=days[now.weekday()]
    day_number=now.day
    month_name=months[now.month]
    year=now.year
    time=now.strftime('%H:%M:%S')
    full_date=f"{day_name}, {day_number} {month_name} {year}"
    
    html_part="<section><h2>Data si ora</h2>"
    
    if show_type == 'zi':
        html_part+=f"<p>{full_date}</p>"
    elif show_type == 'timp':
        html_part+=f"<p>{time}</p>"
    else:
        html_part+=f"<p>{full_date}, {time}</p>"
        
    html_part+="</section>"
    return html_part


def index(request):
    return render(request, 'products/index.html')

def despre(request):
    return render(request, 'products/about.html')

def produse(request):
    
    lista_produse = Produs.objects.all()
    
    produse_cu_discount = []
    
    for produs in lista_produse:
        discount_activ = Discount.objects.filter(
            produs=produs,
            activ=True,
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
        
        produse_cu_discount.append(produs)
    
    context = {
        'produse': produse_cu_discount
    }
    
    return render(request, 'products/produse.html', context)

def contact(request):
    return render(request, 'products/in_lucru.html')

def cos_virtual(request):
    return render(request, 'products/in_lucru.html')

def info(request):
    date_param = request.GET.get('data')
    date_section = None
    
    if date_param:
        date_section = show_data(date_param)
    
    params = list(request.GET.keys())
    num_params = len(params)
    
    context = {
        'sectiune_data': date_section,
        'numar_parametri': num_params,
        'nume_parametri': ', '.join(params) if params else 'Niciun parametru'
    }
    
    return render(request, 'products/info.html', context)

def log(request):
    html = "<h1>Log Accesari</h1>"
    html += f"<h2>Total accesari: {len(visits_list)}</h2>"
    
    accesari_param = request.GET.get('accesari')
    
    if accesari_param == 'detalii':
        html += "<h3>Detalii Accesari (Data si Ora)</h3>"
        html += "<ul>"
        for visit in visits_list:
            html += f"<li>ID {visit.id}: {visit.data('%d/%m/%Y %H:%M:%S')} - {visit.pagina()}</li>"
        html += "</ul>"
    
    if accesari_param == 'nr':
        html += f"<section style='background:#d1ecf1; padding:15px; margin:20px 0;'>"
        html += f"<h3>Numar de accesari de cand a fost pornit serverul: {len(visits_list)}</h3>"
        html += f"</section>"
    
    visits_to_show = visits_list
    
    last_n = request.GET.get('ultimele')
    if last_n:
        try:
            n = int(last_n)
            k = len(visits_list)
            
            if n > k:
                html += f"<p style='color:red;'><strong>Exista doar {k} accesari fata de {n} accesari cerute</strong></p>"
                visits_to_show = visits_list
            else:
                visits_to_show = visits_list[-n:]
        except ValueError:
            html += "<p style='color:red;'><strong>Eroare: parametrul 'ultimele' trebuie sa fie un numar intreg!</strong></p>"
    
    iduri_params = request.GET.getlist('iduri')
    if iduri_params:
        ids_list = []
        for group in iduri_params:
            ids_list.extend(group.split(','))
        
        allow_duplicates = request.GET.get('dubluri', 'false')
        if allow_duplicates != 'true':
            unique_ids = []
            for id_str in ids_list:
                if id_str not in unique_ids:
                    unique_ids.append(id_str)
            ids_list = unique_ids
        
        filtered_visits = []
        for id_str in ids_list:
            try:
                id_int = int(id_str)
                visit = next((v for v in visits_list if v.id == id_int), None)
                if visit:
                    filtered_visits.append(visit)
            except ValueError:
                pass
        
        visits_to_show = filtered_visits
        html += f"<p style='color:blue;'><strong>Filtru activ: afisare ID-uri: {', '.join(ids_list)}</strong></p>"
    
    table_param = request.GET.get('tabel')
    show_as_table = False
    table_columns = []
    
    if table_param:
        show_as_table = True
        if table_param == 'tot':
            table_columns = ['id', 'ip_client', 'url', 'data']
        else:
            table_columns = table_param.split(',')
    
    html += "<hr>"
    
    if show_as_table:
        html += "<table border='1' style='border-collapse:collapse; width:100%;'>"
        html += "<thead><tr>"
        for col in table_columns:
            html += f"<th style='padding:10px; background:#34495e; color:white;'>{col.upper()}</th>"
        html += "</tr></thead>"
        html += "<tbody>"
        
        for visit in visits_to_show:
            html += "<tr>"
            for col in table_columns:
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
    
    if not visits_to_show:
        html += "<p>Nu exista accesari de afisat.</p>"
    
    if visits_list:
        from collections import Counter
        
        pages = [visit.pagina() for visit in visits_list]
        counter = Counter(pages)
        
        if counter:
            most_accessed = counter.most_common(1)[0]
            least_accessed = counter.most_common()[-1]
            
            html += "<hr>"
            html += "<div style='display:flex; justify-content:space-between; margin:30px 0;'>"
            
            html += "<div style='flex:1; margin:0 10px; padding:20px; background:blue; color:white; border-radius:10px; text-align:center;'>"
            html += "<h3 style='margin:0 0 10px 0;'>CEL MAI MULT ACCESATA</h3>"
            html += f"<p style='margin:0; font-size:24px; font-weight:bold;'>{most_accessed[0]}</p>"
            html += f"<small>({most_accessed[1]} accesari)</small>"
            html += "</div>"
            
            html += "<div style='flex:1; margin:0 10px; padding:20px; background:blue; color:white; border-radius:10px; text-align:center;'>"
            html += "<h3 style='margin:0 0 10px 0;'>CEL MAI PUTIN ACCESATA</h3>"
            html += f"<p style='margin:0; font-size:24px; font-weight:bold;'>{least_accessed[0]}</p>"
            html += f"<small>({least_accessed[1]} accesari)</small>"
            html += "</div>"
            
            html += "</div>"
    
    return render(request, 'products/log.html', {'log_html': html})