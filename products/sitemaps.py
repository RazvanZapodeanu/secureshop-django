from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.urls import reverse
from .models import Produs, Categorie


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'
    
    def items(self):
        return ['index', 'despre', 'produse', 'contact']
    
    def location(self, item):
        return reverse(item)


class ProdusSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8
    
    def items(self):
        return Produs.objects.filter(disponibil=True)
    
    def lastmod(self, obj):
        return None
    
    def location(self, obj):
        return reverse('detaliu_produs', kwargs={'slug': obj.slug})


class CategorieSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6
    
    def items(self):
        return Categorie.objects.filter(activa=True)
    
    def location(self, obj):
        return reverse('categorie', kwargs={'slug': obj.slug})


produs_info = {
    'queryset': Produs.objects.filter(disponibil=True),
}

sitemaps = {
    'static': StaticViewSitemap,
    'produse': ProdusSitemap,
    'categorii': CategorieSitemap,
    'produse_generic': GenericSitemap(produs_info, priority=0.7),
}
