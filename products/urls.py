from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('despre/', views.despre, name='despre'),
    path('produse/', views.produse, name='produse'),
    path('produs/<slug:slug>/', views.detaliu_produs, name='detaliu_produs'),
    path('categorii/<slug:slug>/', views.categorie, name='categorie'),
    path('contact/', views.contact, name='contact'),
    path('adauga-produs/', views.adauga_produs, name='adauga_produs'),
    path('cos_virtual/', views.cos_virtual, name='cos_virtual'),
    path('finalizeaza/', views.finalizeaza_comanda, name='finalizeaza_comanda'),
    path('info/', views.info, name='info'),
    path('log/', views.log, name='log'),
    
    path('inregistrare/', views.inregistrare, name='inregistrare'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('confirma_mail/<str:cod>/', views.confirma_mail, name='confirma_mail'),
    path('profil/', views.profil, name='profil'),
    path('schimba-parola/', views.schimba_parola, name='schimba_parola'),
    path('editare-profil/', views.editare_profil, name='editare_profil'),
    
    path('promotii/', views.promotii, name='promotii'),
    path('oferta/', views.oferta, name='oferta'),
    path('acorda-oferta/', views.acorda_oferta, name='acorda_oferta'),
    
    path('cumpara/', views.cumpara, name='cumpara'),
    path('nota/<int:produs_id>/<int:nota>/', views.nota_produs, name='nota_produs'),
    
    path('interzis/', views.interzis, name='interzis'),
]
