from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse

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
    culoare = models.CharField(max_length=7, default="#928C8C")
    icon_class = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural = "Categorii"

class Tag(models.Model):
    CULOARE_CHOICES = [
        ('#FF6B35', 'Portocaliu'),
        ('#00D9FF', 'Cyan'),
        ('#FFB700', 'Galben'),
        ('#00FF41', 'Verde'),
        ('#FF4136', 'Rosu'),
        ('#3498DB', 'Albastru'),
    ]
    nume = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    culoare = models.CharField(max_length=7, choices=CULOARE_CHOICES, default='#3498DB')
    
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
    categorii = models.ManyToManyField(Categorie, blank=True, related_name='produse')
    tag_uri = models.ManyToManyField(Tag, blank=True, related_name='produse')
    

    def get_absolute_url(self):
        return reverse('detaliu_produs', kwargs={'slug': self.slug})
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural = "Produse"

class Specificatie(models.Model):
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name='specificatii')
    nume = models.CharField(max_length=200)
    valoare = models.CharField(max_length=500)
    ordine = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nume
    class Meta:
        verbose_name_plural = "Specificatii"
        ordering = ['ordine']

class Review(models.Model):
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(choices=[(1,'O stea'), (2,'2 stele'), (3,'3 stele'), (4,'4 stele'), (5,'5 stele')])
    titlu = models.CharField(max_length=200)
    comentariu = models.TextField()
    nume_client = models.CharField(max_length=200)
    verificat = models.BooleanField(default=False)
    data_review = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.rating} stele - {self.titlu}"
    class Meta:
        verbose_name_plural = "Reviews"
        ordering = ['-data_review']

class Discount(models.Model):
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name='discounturi')
    procent = models.IntegerField()
    data_inceput = models.DateTimeField()
    data_sfarsit = models.DateTimeField()
    activ = models.BooleanField(default=True)
    
    def __str__(self):
        return f"-{self.procent}% pentru {self.produs.nume}"
    class Meta:
        verbose_name_plural = "Discounturi"
        ordering = ['-data_inceput']


class Utilizator(AbstractUser):
    telefon = models.CharField(max_length=15, blank=True, null=True)
    adresa = models.CharField(max_length=300, blank=True, null=True)
    oras = models.CharField(max_length=100, blank=True, null=True)
    judet = models.CharField(max_length=100, blank=True, null=True)
    cod_postal = models.CharField(max_length=10, blank=True, null=True)
    data_nasterii = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    cod = models.CharField(max_length=100, blank=True, null=True)
    email_confirmat = models.BooleanField(default=False)
    blocat = models.BooleanField(default=False)
    
    notificare_campuri_lipsa = models.BooleanField(default=False)
    ultima_notificare_campuri = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Utilizator"
        verbose_name_plural = "Utilizatori"
    
    def __str__(self):
        return self.username


class Vizualizare(models.Model):
    utilizator = models.ForeignKey(Utilizator, on_delete=models.CASCADE, related_name='vizualizari')
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name='vizualizari')
    data_vizualizare = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vizualizare"
        verbose_name_plural = "Vizualizari"
        ordering = ['-data_vizualizare']


class Promotie(models.Model):
    nume = models.CharField(max_length=200)
    data_creare = models.DateTimeField(auto_now_add=True)
    data_expirare = models.DateTimeField()
    descriere = models.TextField(blank=True)
    procent_reducere = models.IntegerField(default=0)
    categorii = models.ManyToManyField(Categorie, related_name='promotii')
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Promotie"
        verbose_name_plural = "Promotii"
    
    def __str__(self):
        return self.nume


class Comanda(models.Model):
    STARE_CHOICES = [
        ('asteptare', 'In asteptare'),
        ('procesare', 'In procesare'),
        ('expediat', 'Expediat'),
        ('livrat', 'Livrat'),
        ('anulat', 'Anulat'),
    ]
    
    utilizator = models.ForeignKey(Utilizator, on_delete=models.CASCADE, related_name='comenzi')
    data_comanda = models.DateTimeField(auto_now_add=True)
    stare = models.CharField(max_length=20, choices=STARE_CHOICES, default='asteptare')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    adresa_livrare = models.TextField()
    observatii = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Comanda"
        verbose_name_plural = "Comenzi"
        ordering = ['-data_comanda']
    
    def __str__(self):
        return f"Comanda #{self.id} - {self.utilizator.username}"


class ProdusComanda(models.Model):
    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='produse_comanda')
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE)
    cantitate = models.IntegerField(default=1)
    pret_unitar = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Produs Comanda"
        verbose_name_plural = "Produse Comenzi"
    
    @property
    def subtotal(self):
        return self.cantitate * self.pret_unitar


class Nota(models.Model):
    utilizator = models.ForeignKey(Utilizator, on_delete=models.CASCADE, related_name='note')
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name='note')
    nota = models.IntegerField(choices=[(i, f'{i} stele') for i in range(1, 6)])
    data_notare = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Note"
        unique_together = ['utilizator', 'produs']


class IncercareLagare(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    data_incercare = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Incercare Logare"
        verbose_name_plural = "Incercari Logare"
