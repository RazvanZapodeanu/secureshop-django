from django.db import models
from colorfield.fields import ColorField

class Producator(models.Model):
    nume = models.CharField(max_length=200)
    tara_origine = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='producatori/', blank=True, null=True)
    descriere = models.TextField(blank=True)
    activ = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nume 
    class Meta:
        verbose_name_plural = "Producatori"

class Categorie(models.Model):
    nume = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descriere = models.TextField(blank=True)
    imagine = models.ImageField(upload_to='categorii/', blank=True, null=True)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural = "Categorii"
class Tag(models.Model):
    nume = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    culoare = ColorField(default='#3498DB')
    
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural = "Tag-uri"
class Produs(models.Model):
    producator = models.ForeignKey(Producator, on_delete=models.CASCADE, related_name='produse')
    nume = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descriere_scurta = models.CharField(max_length=500, blank=True)
    descriere_lunga = models.TextField(blank=True)
    pret = models.DecimalField(max_digits=10, decimal_places=2)
    pret_vechi = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cod_produs = models.CharField(max_length=100, unique=True)
    imagine = models.ImageField(upload_to='produse/')
    stoc = models.IntegerField(default=0)
    disponibil = models.BooleanField(default=True)
    categorii = models.ManyToManyField(Categorie, blank=True,  related_name='produse')
    tag_uri= models.ManyToManyField(Tag, blank=True, related_name='produse')
    
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural="Produse"
class Specificatie(models.Model):
    produs = models.ForeignKey(
        Produs,
        on_delete=models.CASCADE,
        related_name='specificatii'
    )
    nume = models.CharField(max_length=200)
    valoare = models.CharField(max_length=500)
    ordine = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural="Specificatii"
        ordering=['ordine']
class Review(models.Model):
    produs = models.ForeignKey(
        Produs,
        on_delete=models.CASCADE,
        related_name='review'
    )
    rating = models.IntegerField(
        choices=[(1,'O stea'), (2,'2 stele'), 
                (3,'3 stele'), (4,'4 stele'), 
                (5,'5 stele')]
    )
    titlu = models.CharField(max_length=200)
    comentariu = models.TextField()
    nume_client = models.CharField(max_length=200)
    verificat = models.BooleanField(default=False)
    data_review = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.rating} stele - {self.titlu}"
    class Meta:
        verbose_name_plural="Reviews"
        ordering=['-data_review']
class Discount(models.Model):
    produs = models.ForeignKey(
        Produs,
        on_delete=models.CASCADE,
        related_name='discounturi'
    )
    procent = models.IntegerField()
    data_inceput = models.DateTimeField()
    data_sfarsit = models.DateTimeField()
    activ = models.BooleanField(default=True)
    
    def __str__(self):
        return f"-{self.procent}% pentru {self.produs.nume}"
    class Meta:
        verbose_name_plural="Discounturi"
        ordering=['-data_inceput']
    