from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
from django.core.mail import send_mass_mail
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('django')


def sterge_utilizatori_neconfirmati():
    from .models import Utilizator
    
    utilizatori = Utilizator.objects.filter(email_confirmat=False)
    count = utilizatori.count()
    
    for user in utilizatori:
        logger.warning(f'Se sterge utilizatorul neconfirmat: {user.username}')
        user.delete()
    
    if count > 0:
        logger.info(f'Au fost stersi {count} utilizatori neconfirmati')


def trimite_newsletter():
    from .models import Utilizator, Produs
    import random
    
    threshold = timezone.now() - timedelta(minutes=settings.NEWSLETTER_MINUTES_OLD)
    utilizatori = Utilizator.objects.filter(
        email_confirmat=True,
        date_joined__lte=threshold
    )
    
    produse = list(Produs.objects.filter(disponibil=True, stoc__gt=0)[:5])
    
    messages = []
    for user in utilizatori:
        if produse:
            produs = random.choice(produse)
            subiect = f'Newsletter Secured Systems - {timezone.now().strftime("%d/%m/%Y")}'
            mesaj = f'''
Salut {user.first_name or user.username},

Iata o recomandare pentru tine: {produs.nume}
Pret: {produs.pret} LEI

Viziteaza site-ul nostru pentru mai multe oferte!

Cu stima,
Echipa Secured Systems
            '''
            messages.append((subiect, mesaj, settings.DEFAULT_FROM_EMAIL, [user.email]))
    
    if messages:
        send_mass_mail(messages, fail_silently=True)
        logger.info(f'Newsletter trimis la {len(messages)} utilizatori')


def actualizeaza_stocuri():
    from .models import Produs
    
    produse_actualizate = 0
    for produs in Produs.objects.all():
        if produs.stoc == 0 and produs.disponibil:
            produs.disponibil = False
            produs.save()
            produse_actualizate += 1
        elif produs.stoc > 0 and not produs.disponibil:
            produs.disponibil = True
            produs.save()
            produse_actualizate += 1
    
    if produse_actualizate > 0:
        logger.info(f'Au fost actualizate {produse_actualizate} produse')


def notifica_campuri_lipsa():
    from .models import Utilizator
    
    campuri_importante = ['telefon', 'adresa']
    threshold = timezone.now() - timedelta(days=settings.NZL)
    
    utilizatori = Utilizator.objects.filter(
        email_confirmat=True
    ).exclude(
        ultima_notificare_campuri__gte=threshold
    )
    
    for user in utilizatori:
        lipsa = []
        for camp in campuri_importante:
            if not getattr(user, camp):
                lipsa.append(camp)
        
        if lipsa:
            user.notificare_campuri_lipsa = True
            user.ultima_notificare_campuri = timezone.now()
            user.save()
            logger.debug(f'Notificare campuri lipsa pentru: {user.username}')


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'default')
    
    scheduler.add_job(
        sterge_utilizatori_neconfirmati,
        'interval',
        minutes=settings.K_MINUTE_STERGERE_NECONFIRMATI,
        id='sterge_neconfirmati',
        replace_existing=True
    )
    
    scheduler.add_job(
        trimite_newsletter,
        'cron',
        day_of_week=settings.NEWSLETTER_DAY[:3].lower(),
        hour=settings.NEWSLETTER_HOUR,
        id='newsletter',
        replace_existing=True
    )
    
    scheduler.add_job(
        actualizeaza_stocuri,
        'interval',
        minutes=30,
        id='actualizeaza_stocuri',
        replace_existing=True
    )
    
    scheduler.add_job(
        notifica_campuri_lipsa,
        'cron',
        hour=9,
        id='notifica_campuri',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info('Scheduler pornit')
