from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from datetime import datetime, date
import re
from .models import Producator, Categorie, Tag, Produs, Utilizator, Promotie


def validare_major(value):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError('Expeditorul trebuie sa fie major (peste 18 ani)')


def validare_mesaj_cuvinte(value):
    cuvinte = re.findall(r'\w+', value)
    nr_cuvinte = len(cuvinte)
    if nr_cuvinte < 5 or nr_cuvinte > 100:
        raise ValidationError('Mesajul trebuie sa contina intre 5 si 100 cuvinte')
    for cuvant in cuvinte:
        if len(cuvant) > 15:
            raise ValidationError('Lungimea unui cuvant in mesaj nu trebuie sa depaseasca 15 caractere')


def validare_fara_linkuri(value):
    if 'http://' in value or 'https://' in value:
        raise ValidationError('Textul nu poate contine linkuri')


def validare_cnp_cifre(value):
    if value and not value.isdigit():
        raise ValidationError('CNP-ul trebuie sa contina doar cifre')


def validare_cnp_format(value):
    if not value:
        return
    if len(value) != 13:
        return
    primul_caracter = value[0]
    if primul_caracter not in ['1', '2', '5', '6']:
        raise ValidationError('CNP-ul trebuie sa inceapa cu 1, 2, 5 sau 6')
    an = int(value[1:3])
    luna = int(value[3:5])
    zi = int(value[5:7])
    if primul_caracter in ['1', '2']:
        an += 1900
    elif primul_caracter in ['5', '6']:
        an += 2000
    try:
        date(an, luna, zi)
    except ValueError:
        raise ValidationError('CNP-ul contine o data invalida')


def validare_email_temporar(value):
    domenii_interzise = ['guerillamail.com', 'yopmail.com']
    domeniu = value.split('@')[-1]
    if domeniu in domenii_interzise:
        raise ValidationError('Nu sunt permise adresele de email temporare')


def validare_text_formatat(value):
    if not value:
        return
    if not re.match(r'^[A-ZĂÂÎȘȚ]', value):
        raise ValidationError('Textul trebuie sa inceapa cu litera mare')
    if not re.match(r'^[A-ZĂÂÎȘȚa-zăâîșț \-]+$', value):
        raise ValidationError('Textul poate contine doar litere, spatii si cratima')


def validare_litera_mare_dupa_separator(value):
    if not value:
        return
    pattern = r'[\s\-][a-zăâîșț]'
    if re.search(pattern, value):
        raise ValidationError('Dupa spatiu sau cratima trebuie sa fie litera mare')


def validare_nume_produs_litere(value):
    if not value[0].isalpha():
        raise ValidationError('Numele produsului trebuie sa inceapa cu o litera!')


def validare_lungime_minima(value):
    if len(value.strip()) < 3:
        raise ValidationError('Textul trebuie sa aiba cel putin 3 caractere!')


def validare_fara_caractere_speciale(value):
    caractere_speciale = ['@', '#', '$', '%', '^', '&', '*']
    for char in caractere_speciale:
        if char in value:
            raise ValidationError(f'Nu sunt permise caractere speciale precum {char}!')


def validare_cod_produs_format(value):
    if not re.match(r'^[A-Z]{2,4}-\d{4,6}$', value):
        raise ValidationError('Codul produsului trebuie sa fie in format: ABC-1234 (2-4 litere mari, liniuta, 4-6 cifre)!')


def validare_stoc_pozitiv(value):
    if value < 0:
        raise ValidationError('Stocul nu poate fi negativ!')
    if value > 10000:
        raise ValidationError('Stocul nu poate depasi 10.000 unitati!')


def validare_telefon(value):
    if value and not re.match(r'^(\+4|0)[0-9]{9,10}$', value):
        raise ValidationError('Numarul de telefon trebuie sa fie in format valid (ex: 0721234567 sau +40721234567)')


def validare_cod_postal(value):
    if value and not re.match(r'^\d{6}$', value):
        raise ValidationError('Codul postal trebuie sa contina exact 6 cifre')


def validare_varsta_minima(value):
    if value:
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 16:
            raise ValidationError('Trebuie sa ai cel putin 16 ani pentru a te inregistra')


class AdaugaProdusForm(forms.ModelForm):
    pret_cumparare = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label='Pret de achizitie (LEI)',
        help_text='Pretul la care ai cumparat produsul de la furnizor',
        localize=False,
        widget=forms.NumberInput(attrs={'placeholder': '1000', 'class': 'form-input', 'step': '0.01'})
    )
    
    adaos_comercial = forms.DecimalField(
        required=True,
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        label='Adaos comercial (%)',
        help_text='Procentul de profit pe care vrei sa-l adaugi (0-100%)',
        localize=False,
        widget=forms.NumberInput(attrs={'placeholder': '25', 'class': 'form-input', 'step': '0.01'})
    )
    
    class Meta:
        model = Produs
        fields = ['producator', 'nume', 'descriere_scurta', 'descriere_lunga', 
                'cod_produs', 'imagine', 'stoc', 'categorii', 'tag_uri']
        labels = {
            'nume': 'Denumire produs',
            'descriere_scurta': 'Descriere scurta (pentru preview)',
            'cod_produs': 'Cod unic produs',
            'stoc': 'Cantitate disponibila',
        }
        widgets = {
            'nume': forms.TextInput(attrs={'placeholder': 'Ex: HEV Suit Mark VI', 'class': 'form-input'}),
            'descriere_scurta': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descriere scurta (max 500 caractere)', 'class': 'form-input'}),
            'descriere_lunga': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Descriere detaliata a produsului...', 'class': 'form-input'}),
            'cod_produs': forms.TextInput(attrs={'placeholder': 'HEV-001234', 'class': 'form-input'}),
            'stoc': forms.NumberInput(attrs={'placeholder': '0', 'class': 'form-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nume'].validators = [validare_nume_produs_litere, validare_lungime_minima]
        self.fields['descriere_scurta'].validators = [validare_lungime_minima]
    
    def clean_cod_produs(self):
        cod = self.cleaned_data.get('cod_produs')
        validare_cod_produs_format(cod)
        return cod.upper()
    
    def clean_stoc(self):
        stoc = self.cleaned_data.get('stoc')
        validare_stoc_pozitiv(stoc)
        return stoc
    
    def clean_descriere_scurta(self):
        desc = self.cleaned_data.get('descriere_scurta')
        validare_fara_caractere_speciale(desc)
        return desc
    
    def clean(self):
        cleaned_data = super().clean()
        pret_cumparare = cleaned_data.get('pret_cumparare')
        adaos = cleaned_data.get('adaos_comercial')
        stoc = cleaned_data.get('stoc')
        
        if pret_cumparare and adaos:
            if pret_cumparare < 10 and adaos > 50:
                raise ValidationError('Pentru produse sub 10 LEI, adaosul comercial nu poate depasi 50%!')
        
        return cleaned_data
    
    def save(self, commit=True):
        produs = super().save(commit=False)
        pret_cumparare = self.cleaned_data.get('pret_cumparare')
        adaos = self.cleaned_data.get('adaos_comercial')
        
        if pret_cumparare and adaos:
            produs.pret = pret_cumparare * (1 + adaos / 100)
            produs.pret_vechi = None
        
        produs.disponibil = produs.stoc > 0
        
        from django.utils.text import slugify
        if not produs.slug:
            produs.slug = slugify(produs.nume)
        
        if commit:
            produs.save()
            self.save_m2m()
        
        return produs


class FiltruProduseForm(forms.Form):
    nume = forms.CharField(required=False, label='Nume produs', 
                        widget=forms.TextInput(attrs={'placeholder': 'Cauta produs...', 'class': 'form-input'}))
    
    producator = forms.ModelChoiceField(queryset=Producator.objects.filter(activ=True), required=False, 
                                        label='Producator', empty_label='Toti producatorii',
                                        widget=forms.Select(attrs={'class': 'form-select'}))
    
    categorie = forms.ModelChoiceField(queryset=Categorie.objects.filter(activa=True), required=False,
                                    label='Categorie', empty_label='Toate categoriile',
                                    widget=forms.Select(attrs={'class': 'form-select'}))
    
    tag = forms.ModelChoiceField(queryset=Tag.objects.all(), required=False, label='Tag', empty_label='Toate tag-urile',
                                widget=forms.Select(attrs={'class': 'form-select'}))
    
    cod_produs = forms.CharField(required=False, label='Cod produs',
                                widget=forms.TextInput(attrs={'placeholder': 'Ex: HEV-001', 'class': 'form-input'}))
    
    pret_min = forms.DecimalField(required=False, min_value=0, label='Pret minim',
                                widget=forms.NumberInput(attrs={'placeholder': '0', 'class': 'form-input'}))
    
    pret_max = forms.DecimalField(required=False, min_value=0, label='Pret maxim',
                                widget=forms.NumberInput(attrs={'placeholder': '9999', 'class': 'form-input'}))
    
    stoc_min = forms.IntegerField(required=False, min_value=0, label='Stoc minim',
                                widget=forms.NumberInput(attrs={'placeholder': '0', 'class': 'form-input'}))
    
    stoc_max = forms.IntegerField(required=False, min_value=0, label='Stoc maxim',
                                widget=forms.NumberInput(attrs={'placeholder': '9999', 'class': 'form-input'}))
    
    disponibil = forms.ChoiceField(choices=[('', 'Toate'), ('True', 'Disponibil'), ('False', 'Indisponibil')],
                                required=False, label='Disponibilitate',
                                widget=forms.Select(attrs={'class': 'form-select'}))
    
    produse_pe_pagina = forms.IntegerField(required=False, initial=6, min_value=1, max_value=50,
                                        label='Produse per pagina',
                                        widget=forms.NumberInput(attrs={'placeholder': '6', 'class': 'form-input'}))
    
    categorie_fixa = forms.IntegerField(required=False, widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        categorie_fixa_id = kwargs.pop('categorie_fixa', None)
        super().__init__(*args, **kwargs)
        if categorie_fixa_id:
            self.fields['categorie'].initial = categorie_fixa_id
            self.fields['categorie'].widget = forms.HiddenInput()
            self.fields['categorie_fixa'].initial = categorie_fixa_id
    
    def clean_pret_max(self):
        pret_min = self.cleaned_data.get('pret_min')
        pret_max = self.cleaned_data.get('pret_max')
        if pret_min and pret_max and pret_max < pret_min:
            raise ValidationError('Pretul maxim trebuie sa fie mai mare sau egal cu pretul minim!')
        return pret_max
    
    def clean_stoc_max(self):
        stoc_min = self.cleaned_data.get('stoc_min')
        stoc_max = self.cleaned_data.get('stoc_max')
        if stoc_min is not None and stoc_max is not None and stoc_max < stoc_min:
            raise ValidationError('Stocul maxim trebuie sa fie mai mare sau egal cu stocul minim!')
        return stoc_max
    
    def clean_produse_pe_pagina(self):
        produse_pe_pagina = self.cleaned_data.get('produse_pe_pagina')
        if produse_pe_pagina:
            if produse_pe_pagina < 1:
                raise ValidationError('Trebuie sa afisezi cel putin 1 produs pe pagina!')
            if produse_pe_pagina > 50:
                raise ValidationError('Nu poti afisa mai mult de 50 de produse pe pagina pentru performanta optima!')
        return produse_pe_pagina
    
    def clean(self):
        cleaned_data = super().clean()
        categorie = cleaned_data.get('categorie')
        categorie_fixa = cleaned_data.get('categorie_fixa')
        if categorie_fixa and categorie:
            if categorie.id != categorie_fixa:
                raise ValidationError('Nu puteti modifica categoria pe aceasta pagina! Categoria este fixata pentru aceasta sectiune.')
        return cleaned_data


class ContactForm(forms.Form):
    TIPURI_MESAJ = [
        ('neselectat', 'Neselectat'),
        ('reclamatie', 'Reclamatie'),
        ('intrebare', 'Intrebare'),
        ('review', 'Review'),
        ('cerere', 'Cerere'),
        ('programare', 'Programare'),
    ]
    
    nume = forms.CharField(max_length=10, required=True, validators=[validare_text_formatat, validare_litera_mare_dupa_separator])
    prenume = forms.CharField(max_length=10, required=False, validators=[validare_text_formatat, validare_litera_mare_dupa_separator])
    cnp = forms.CharField(max_length=13, min_length=13, required=False, validators=[validare_cnp_cifre, validare_cnp_format])
    data_nasterii = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}), validators=[validare_major])
    email = forms.EmailField(required=True, validators=[validare_email_temporar])
    confirmare_email = forms.EmailField(required=True, label='Confirmare e-mail')
    tip_mesaj = forms.ChoiceField(choices=TIPURI_MESAJ, initial='neselectat', required=True)
    subiect = forms.CharField(max_length=100, required=True, validators=[validare_fara_linkuri, validare_text_formatat, validare_litera_mare_dupa_separator])
    minim_zile_asteptare = forms.IntegerField(required=True, min_value=0, max_value=30, label='Minim zile asteptare',
                                            help_text='Pentru review-uri/cereri minimul de zile de asteptare trebuie setat de la 4 incolo iar pentru cereri/intrebari de la 2 incolo. Maximul e 30.')
    mesaj = forms.CharField(widget=forms.Textarea, required=True, validators=[validare_mesaj_cuvinte, validare_fara_linkuri],
                        label='Mesaj (va rugam sa va semnati)')
    
    def clean_tip_mesaj(self):
        tip = self.cleaned_data.get('tip_mesaj')
        if tip == 'neselectat':
            raise ValidationError('Trebuie sa selectati un tip de mesaj')
        return tip
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirmare = cleaned_data.get('confirmare_email')
        if email and confirmare and email != confirmare:
            raise ValidationError('E-mailul si confirmarea e-mailului trebuie sa coincida')
        
        mesaj = cleaned_data.get('mesaj')
        nume = cleaned_data.get('nume')
        if mesaj and nume:
            cuvinte = re.findall(r'\w+', mesaj)
            if cuvinte and cuvinte[-1].lower() != nume.lower():
                raise ValidationError('Mesajul trebuie sa se incheie cu numele dumneavoastra (semnatura)')
        
        tip_mesaj = cleaned_data.get('tip_mesaj')
        zile = cleaned_data.get('minim_zile_asteptare')
        if tip_mesaj and zile is not None:
            if tip_mesaj in ['review', 'cerere'] and zile < 4:
                raise ValidationError('Pentru review-uri si cereri minimul de zile de asteptare este 4')
            if tip_mesaj in ['cerere', 'intrebare'] and zile < 2:
                raise ValidationError('Pentru cereri si intrebari minimul de zile de asteptare este 2')
        
        cnp = cleaned_data.get('cnp')
        data_nasterii = cleaned_data.get('data_nasterii')
        if cnp and data_nasterii and len(cnp) == 13:
            an_cnp = int(cnp[1:3])
            luna_cnp = int(cnp[3:5])
            zi_cnp = int(cnp[5:7])
            primul_caracter = cnp[0]
            if primul_caracter in ['1', '2']:
                an_cnp += 1900
            elif primul_caracter in ['5', '6']:
                an_cnp += 2000
            if (data_nasterii.year != an_cnp or data_nasterii.month != luna_cnp or data_nasterii.day != zi_cnp):
                raise ValidationError('CNP-ul nu corespunde cu data nasterii')
        
        return cleaned_data


class InregistrareForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='Prenume')
    last_name = forms.CharField(max_length=30, required=True, label='Nume')
    telefon = forms.CharField(max_length=15, required=False, validators=[validare_telefon])
    adresa = forms.CharField(max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2}))
    oras = forms.CharField(max_length=100, required=False)
    judet = forms.CharField(max_length=100, required=False)
    cod_postal = forms.CharField(max_length=10, required=False, validators=[validare_cod_postal])
    data_nasterii = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), validators=[validare_varsta_minima])
    
    class Meta:
        model = Utilizator
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                'telefon', 'adresa', 'oras', 'judet', 'cod_postal', 'data_nasterii']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username.lower() == 'admin':
            from django.core.mail import mail_admins
            mail_admins(
                'Cineva incearca sa ne preia site-ul',
                f'S-a incercat inregistrarea cu username-ul admin de la email: {self.data.get("email", "necunoscut")}',
                html_message=f'<h1 style="color:red;">Cineva incearca sa ne preia site-ul</h1><p>S-a incercat inregistrarea cu username-ul admin de la email: {self.data.get("email", "necunoscut")}</p>'
            )
            raise ValidationError('Acest username nu este disponibil')
        return username


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, label='Pastreaza-ma logat', initial=False)
    
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.email_confirmat:
            raise ValidationError('Trebuie sa va confirmati emailul inainte de a va loga. Verificati inbox-ul.')
        if user.blocat:
            raise ValidationError('Contul dumneavoastra a fost blocat. Contactati administratorul pentru mai multe detalii.')


class SchimbaParolaForm(PasswordChangeForm):
    pass


class EditareProfilForm(forms.ModelForm):
    class Meta:
        model = Utilizator
        fields = ['first_name', 'last_name', 'email', 'telefon', 'adresa', 'oras', 'judet', 'cod_postal', 'data_nasterii']
        widgets = {
            'adresa': forms.Textarea(attrs={'rows': 2}),
            'data_nasterii': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telefon'].validators = [validare_telefon]
        self.fields['cod_postal'].validators = [validare_cod_postal]


class PromotieForm(forms.ModelForm):
    categorii = forms.ModelMultipleChoiceField(
        queryset=Categorie.objects.filter(activa=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Categorii pentru promotie'
    )
    
    class Meta:
        model = Promotie
        fields = ['nume', 'descriere', 'procent_reducere', 'data_expirare', 'categorii']
        widgets = {
            'data_expirare': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descriere': forms.Textarea(attrs={'rows': 3}),
        }
