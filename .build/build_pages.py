#!/usr/bin/env python3
"""Сборка страниц для поисковиков из index.html.

index.html – единственный исходник. Скрипт:
  1) дописывает в него SEO-шапку (canonical, Open Graph, разметку организации);
  2) делает копии /kids/, /adults/, /afisha/, /team/, /svedeniya/ и страницы курсов
     со своим заголовком и описанием и с нужным разделом, видимым без JS;
  3) пишет sitemap.xml и robots.txt.
Запуск из корня сайта:  python3 .build/build_pages.py
Курсы берутся из админки (https://proneiroclub.ru/api/public/content).
"""
import html, json, os, re, sys, urllib.request, datetime

SITE = 'https://proneiroclub.ru'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OG_IMG = SITE + '/img/club/zal.jpg'
DESC_HOME = 'ProНейро – клуб практического искусственного интеллекта в центре Твери. Нейросети на практике для взрослых, детей 7–14 лет и бизнеса: курсы, интенсивы и бесплатные встречи-знакомства.'
PAGES = {
    'kids': ('Курсы по нейросетям и программированию для детей 7–14 лет в Твери – proнейро',
             'Курсы для детей 7–14 лет в Твери: нейросети и творчество, дизайн, Roblox и Python с ИИ. Очные занятия в студии клуба ProНейро, бесплатное Нейро-воскресенье для знакомства.'),
    'adults': ('Курсы нейросетей для взрослых в Твери – proнейро',
               'Нейросети для работы и своего дела: бесплатная Нейро-суббота, интенсивы на 2 часа, базовый курс и обучение команд. Клуб ProНейро в центре Твери.'),
    'afisha': ('Афиша клуба: встречи, интенсивы и курсы – proнейро',
               'Все события клуба ProНейро в Твери: бесплатные встречи-знакомства, мастер-классы, интенсивы и старты курсов для взрослых и детей.'),
    'team': ('Команда клуба ProНейро – основатель и преподаватели',
             'Кто ведёт занятия в клубе практического ИИ ProНейро в Твери: основатель клуба, преподаватели курсов для взрослых и педагоги для детей.'),
    'svedeniya': ('Сведения об образовательной организации – proнейро',
                  'Сведения об образовательной организации ProНейро: реквизиты, документы, материально-техническое обеспечение.'),
}

def esc(t): return html.escape(t, quote=True)

def head_block(title, desc, url):
    org = {
        "@context": "https://schema.org", "@type": "EducationalOrganization",
        "name": "ProНейро – клуб практического ИИ", "alternateName": "proнейро",
        "url": SITE + '/', "logo": SITE + '/img/emblem.png', "image": OG_IMG,
        "telephone": "+7-904-000-12-13", "email": "Grand.tver@mail.ru", "sameAs": ["https://vk.ru/club241086009"],
        "address": {"@type": "PostalAddress", "streetAddress": "ул. Новоторжская, д. 18, корп. 1, пом. 48",
                    "addressLocality": "Тверь", "postalCode": "170100", "addressCountry": "RU"},
        "geo": {"@type": "GeoCoordinates", "latitude": 56.858341, "longitude": 35.912965},
    }
    return ('<!--SEO-->\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">\n'
            '<meta property="og:type" content="website">\n<meta property="og:locale" content="ru_RU">\n'
            '<meta property="og:site_name" content="proнейро">\n'
            '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n<meta property="og:image" content="%s">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<script type="application/ld+json">%s</script>\n<!--/SEO-->') % (
        esc(title), esc(desc), url, esc(title), esc(desc), url, OG_IMG, json.dumps(org, ensure_ascii=False))

def set_head(s, title, desc, url):
    s = re.sub(r'<!--SEO-->.*?<!--/SEO-->', '', s, flags=re.S)
    s = re.sub(r'<title>.*?</title>\n?', '', s, flags=re.S)
    s = re.sub(r'<meta name="description"[^>]*>\n?', '', s)
    s = re.sub(r'<meta name="robots"[^>]*>\n?', '', s)
    return s.replace('<meta name="viewport" content="width=device-width, initial-scale=1">',
                     '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + head_block(title, desc, url), 1)

def show(s, page):
    s = re.sub(r'<div data-page="(\w+)"( hidden)?', lambda m: '<div data-page="%s"%s' % (m.group(1), '' if m.group(1) == page else ' hidden'), s)
    return s

def write(rel, s):
    path = os.path.join(ROOT, rel, 'index.html') if rel else os.path.join(ROOT, 'index.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(s)

def main():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    src = set_head(src, 'proнейро – клуб практического ИИ в Твери: нейросети для взрослых и детей', DESC_HOME, SITE + '/')
    src = show(src, 'home')
    write('', src)
    urls = [(SITE + '/', '1.0')]
    for pg, (t, d) in PAGES.items():
        write(pg, show(set_head(src, t, d, '%s/%s/' % (SITE, pg)), pg))
        urls.append(('%s/%s/' % (SITE, pg), '0.8' if pg in ('kids', 'adults') else '0.6'))
    try:
        data = json.load(urllib.request.urlopen(SITE + '/api/public/content', timeout=15))
        courses = data.get('courses', [])
    except Exception as e:
        print('Курсы не загрузились из админки:', e); courses = []
    for c in courses:
        sec = 'kids' if c.get('page') == 'kids' else 'adults'
        who = 'курс для детей 7–14 лет' if sec == 'kids' else 'курс для взрослых'
        t = '%s – %s в Твери – proнейро' % (c['title'], who)
        d = '%s. %s, %s. Клуб ProНейро в центре Твери.' % ((c.get('sub') or c['title']).rstrip('.'), (c.get('length') or '').replace(' · ', ', '), c.get('price') or '')
        write('%s/%s' % (sec, c['id']), show(set_head(src, t, d, '%s/%s/%s/' % (SITE, sec, c['id'])), sec))
        urls.append(('%s/%s/%s/' % (SITE, sec, c['id']), '0.7'))
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += ['  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (u, today, p) for u, p in urls]
    sm.append('</urlset>')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm) + '\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write('''User-agent: *
Disallow: /admin
Disallow: /api/
Disallow: /1/
Disallow: /2/
Disallow: /3/
Disallow: /v1/
Disallow: /v2/
Disallow: /v3/
Disallow: /cards/
Disallow: /variants/
Disallow: /who-test/
Disallow: /afisha-v/

Sitemap: %s/sitemap.xml
''' % SITE)
    print('Страниц:', len(urls))

if __name__ == '__main__':
    main()
