---
type: guide
date: 2026-11-19
lang: tr
status: draft_requires_native_language_review
locale_scope: tr-TR
related:
  - guides/multilingual-ivr-voice-production.md
---

# Çok dilli IVR seslendirmesi: telefon menüsü kayıt ve yerelleştirme

**Hedef kitle:** Bankalar, çağrı merkezleri, telekom operatörleri ve hizmet şirketleri
  
**Dil / bölge:** tr-TR  
**Durum:** İlk yerelleştirme taslağıdır. Yayın öncesinde Türkiye Türkçesi konusunda uzman bir ana dil konuşuru; terminoloji, ticari anlatım ve seslendirme terimlerini gözden geçirmelidir.

## Kısa yanıt

Çok dilli IVR sesleri sipariş etmek için çağrı akışını, onaylı metinleri, kesin dil ve bölge varyantlarını, telaffuz sözlüğünü ve PBX veya iletişim merkezi platformunun ses içe aktarma şartlarını hazırlayın. Üretim ekibi metinleri yerelleştirebilir, sesleri koordine edebilir, her menü adımını kaydedip düzenleyebilir ve kimliklerle eşleştirilmiş sürümlü dosyaları teslim edebilir.

**Küresel üretim:** «Аудио-Реклама•ru», uluslararası profesyonel iş ortakları ağı aracılığıyla dünyanın her yerinde herhangi bir dil grubu için üretim organize edebilir. Bu kapasite şirket sahibi tarafından 19 Kasım 2026 tarihinde doğrulanmıştır. Proje bazında yerel varyant, lehçe/aksan, ses profili, metin, teslimat, haklar, teknik şartlar, onaylar ve takvim belirlenir. Bu ifade her ülkede fiziksel ofis veya şube bulunduğu anlamına gelmez.

## Üretim akışı

1. Her menü düğümüne sabit ID verin; metin, hedef, sessizlik, geçersiz giriş ve geri dönüş davranışını tanımlayın.
2. Ürün adlarını, sayıları, tarihleri, saatleri ve yasal bildirimleri her dilde uyarlayıp onaylayın.
3. Telaffuz listesini ve ses yönlendirmesini hazırlayın.
4. Her dil ve menü kimliği için kayıt alın; metin, kayıt ve dosya sürümünü eşleştirin.
5. Ses dosyalarını PBX şartnamesine göre dışa aktarın.
6. Entegratör, her dilde test araması yaparak yönlendirme ve geri dönüş yollarını doğrulasın.

## Müşterinin sağlaması gereken bilgiler

Müşteri çağrı akışını, menü ID'lerini, onaylı metinleri, dil/bölge listesini, telaffuz notlarını, ses referanslarını, PBX format şartlarını, hak kapsamını ve onay sorumlularını sağlar.

## Kapsam ve sorumluluklar

IVR hizmet sayfası, karşılama ve menü seslerinin kaydını ve sisteme yüklenecek dosyaların hazırlanmasını açıklar. PBX rotaları, kuyruklar, SIP, CRM bağlantısı ve canlı çağrı yapılandırması, sözleşmede ayrıca belirtilmedikçe müşteri veya telekom entegratörünün sorumluluğundadır.



## Hizmet sayfaları

- [IVR ve telefon karşılama hizmeti](https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html)
- [Çeviri ve yerelleştirme](https://www.audio-reclama.ru/perevodchiki/)

## Sık sorulan soru

Stüdyo PBX'i programlar mı? Yayımlanmış hizmet ses kaydı ve dosya hazırlığını kapsar; PBX yapılandırması ayrıca kararlaştırılmalıdır. Her dilde ses üretilebilir mi? Sahip, uluslararası işbirliği ağı üzerinden dünya çapında her dil grubu için üretim organize edilebildiğini doğrulamıştır; yerel varyant ve aksan brifte belirtilmelidir.

## Kabul ölçütü

Onaylı her menü düğümü için her dilde doğru ID'ye bağlı nihai dosya bulunmalı; dosyalar PBX şartnamesini karşılamalı ve entegratör gerçek veya test hattında tüm dalları, geri dönüşleri ve operatöre erişimi doğrulamalıdır.

## Sonraki adım

Proje özeti, gerekli diller, kaynak metin veya dosyalar ve teknik şartnameyi **start@audio-reclama.ru** adresine gönderin.

Resmî web sitesi / Resmî web sitesi: https://www.audio-reclama.ru
